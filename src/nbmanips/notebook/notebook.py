from __future__ import annotations

import json
import os
import re
from contextlib import suppress
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, ClassVar, Iterable, Iterator, TypeVar

import nbconvert
import nbformat
from nbconvert.exporters.exporter import Exporter

try:
    import pygments.util
    from pygments.lexers import get_lexer_by_name
except ImportError:
    pygments = None
    get_lexer_by_name = None


from nbmanips.cell import Cell
from nbmanips.cell.cell_utils import PYGMENTS_SUPPORTED
from nbmanips.notebook.ipynb import (
    dict_to_ipynb,
    get_ipynb_name,
    read_ipynb,
    write_ipynb,
)
from nbmanips.selector import Selector

T = TypeVar("T")


def _get_regex(text: str, case: bool = False, regex: bool = False) -> re.Pattern:
    if not regex:
        text = re.escape(text)

    flags = 0
    flags = (flags & ~re.IGNORECASE) if case else (flags | re.IGNORECASE)

    return re.compile(text, flags)


class Notebook:
    __slots__ = ("raw_nb", "name", "_selector", "_original_path")
    __exporters: ClassVar[dict[str, dict[str, type[Exporter]]]] = {
        "nbconvert": {
            "html": nbconvert.HTMLExporter,
            "slides": nbconvert.SlidesExporter,
            "python": nbconvert.PythonExporter,
            "markdown": nbconvert.MarkdownExporter,
            "script": nbconvert.ScriptExporter,
        }
    }

    def __init__(
        self,
        content: dict | None = None,
        name: str | None = None,
        validate: bool = True,
        copy: bool = True,
    ):
        if content is None:
            content = dict(nbformat.v4.new_notebook())

        if validate:
            self.__validate(content)

        if copy:
            self.raw_nb = deepcopy(content)
        else:
            self.raw_nb = content

        self.name = name
        self._selector = Selector(None)

    def select(self, selector: Any, *args, **kwargs) -> Notebook:
        nb = self.reset_selection()
        nb._selector = self._selector & Selector(selector, *args, **kwargs)
        return nb

    def apply(self, func: Callable[[Cell], Cell | None], neg: bool = False) -> None:
        delete_list = []
        for cell in self.iter_cells(neg):
            num = cell.num
            new_cell = func(cell)
            if new_cell is None:
                delete_list.append(num)
            else:
                self.cells[num] = new_cell.cell

        for num in reversed(delete_list):
            del self.cells[num]

    def map(self, func: Callable[[Cell], T], neg: bool = False) -> list[T]:
        return list(map(func, self.iter_cells(neg)))

    def reset_selection(self) -> Notebook:
        notebook_selection = Notebook(
            self.raw_nb, self.name, validate=False, copy=False
        )

        # Adding Original Notebook Path if defined
        original_path = getattr(self, "_original_path", None)
        if original_path:
            notebook_selection._original_path = original_path

        return notebook_selection

    def iter_cells(self, neg: bool = False) -> Iterator[Cell]:
        return self._selector.iter_cells(self.raw_nb, neg=neg)

    @property
    def cells(self) -> list[dict[str, Any]]:
        return self.raw_nb["cells"]

    @property
    def metadata(self) -> dict[str, Any]:
        return self.raw_nb["metadata"]

    @property
    def used_ids(self) -> set[str]:
        return {cell["id"] for cell in self.cells if "id" in cell}

    def first_cell(self) -> Cell | None:
        """
        Return the first selected cell
        :return:
        """
        for cell in self.iter_cells():
            return cell

    def last_cell(self) -> Cell | None:
        """
        Return the last selected cell
        :return:
        """
        for cell in reversed(list(self.iter_cells())):
            return cell

    def list_cells(self) -> list[Cell]:
        """
        Return a list of the selected cells
        :return:
        """
        return [cell for cell in self.iter_cells()]

    def add_cell(self, cell: Cell, pos: int | None = None) -> None:
        pos = len(self) if pos is None else pos

        new_id = cell.id
        while new_id in self.used_ids:
            new_id = cell.generate_id_candidate()

        cell = cell.get_copy(new_id)
        self.cells.insert(pos, cell.cell)

    def __iter__(self) -> Iterator[Cell]:
        return self.iter_cells()

    def __add__(self, other: Notebook):
        if not isinstance(other, Notebook):
            return NotImplemented

        # Copying the notebook
        raw_nb = {
            key: deepcopy(value) for key, value in self.raw_nb.items() if key != "cells"
        }

        # Creating empty Notebook
        raw_nb["cells"] = []
        new_nb = self.__class__(raw_nb, validate=False, copy=False)

        # Concatenating the notebooks
        for cell in self.list_cells() + other.list_cells():
            new_nb.add_cell(cell)

        return new_nb

    def __mul__(self, other: int):
        if not isinstance(other, int):
            return NotImplemented

        # Copying the notebook
        raw_nb = {
            key: deepcopy(value) for key, value in self.raw_nb.items() if key != "cells"
        }

        # Creating empty Notebook
        raw_nb["cells"] = []
        new_nb = self.__class__(raw_nb, validate=False, copy=False)

        # Concatenating the notebooks
        for _ in range(other):
            for cell in self.iter_cells():
                new_nb.add_cell(cell)
        return new_nb

    def __getitem__(self, item: Any | tuple[Any]) -> Notebook:
        if isinstance(item, tuple):
            return self.select(*item)
        return self.select(item)

    def __len__(self) -> int:
        if self.raw_nb is None or "cells" not in self.raw_nb:
            return 0
        return len(self.list_cells())

    def __repr__(self) -> str:
        if self.name:
            return f'<Notebook "{self.name}">'
        else:
            return "<Notebook>"

    def __str__(self) -> str:
        return "\n".join(str(cell) for cell in self.iter_cells())

    def __and__(self, other: Notebook) -> Notebook:
        if not isinstance(other, Notebook):
            return NotImplemented

        if other.raw_nb is not self.raw_nb:
            raise ValueError("and operator only works with the same Notebook.")

        nb = self.reset_selection()
        nb._selector = self._selector & other._selector
        return nb

    def __or__(self, other: Notebook) -> Notebook:
        if not isinstance(other, Notebook):
            return NotImplemented

        if other.raw_nb is not self.raw_nb:
            raise ValueError("and operator only works with the same Notebook.")

        nb = self.reset_selection()
        nb._selector = self._selector | other._selector
        return nb

    def __invert__(self) -> Notebook:
        nb = self.reset_selection()
        nb._selector = ~self._selector
        return nb

    @staticmethod
    def __validate(content: dict) -> None:
        if not isinstance(content, dict):
            message = (
                f"'content' must be of type 'dict': {type(content).__name__!r} given"
            )
            if isinstance(content, str):
                message += "\nUse Notebook.read(path) to read notebook from file"
            raise ValueError(message)
        nbformat.validate(nbdict=content)

    # == Classic Notebook ==
    def update_cell_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to the selected cells
        :param key: metadata key
        :param value: metadata value
        """
        for cell in self.iter_cells():
            value = deepcopy(value)
            cell.update_metadata(key, value)

    def erase(self) -> None:
        """
        Erase the content of the selected cells
        """
        for cell in self.iter_cells():
            cell.set_source([])

    def erase_output(self, output_types: str | Iterable[str] | None = None) -> None:
        """
        Erase the output content of the selected cells
        """
        for cell in self.iter_cells():
            cell.erase_output(output_types)

    def delete(self) -> None:
        """
        Delete the selected cells
        """
        self.raw_nb["cells"] = [cell.cell for cell in self.iter_cells(neg=True)]

    def keep(self) -> None:
        """
        Delete all the non-selected cells
        """
        self.raw_nb["cells"] = [cell.cell for cell in self.iter_cells()]

    def first(self) -> int | None:
        """
        Return the number of the first selected cell
        :return:
        """
        for cell in self.iter_cells():
            return cell.num

    def last(self) -> int | None:
        """
        Return the number of the last selected cell
        :return:
        """
        for cell in reversed(list(self.iter_cells())):
            return cell.num

    def copy(self, selection: bool = True, crop: bool = True) -> Notebook:
        """
        Copy the notebook instance

        :param selection: keep selection
        :param crop: crop on selection
        :return: a new copy of the notebook
        """
        cp = Notebook(self.raw_nb, self.name, validate=False, copy=True)
        if selection:
            cp._selector = self._selector
            if crop:
                cp.keep()
                cp = cp.reset_selection()
        return cp

    def split(self, *args) -> list[Notebook]:
        """
        Split the notebook based passed selectors (typically cell indexes)

        :param args:
        :return:
        """
        return self.copy().select(args, type="or").split_on_selection()

    def split_on_selection(self) -> list[Notebook]:
        """
        Split the notebook based on the selected cells
        :return:
        """
        cp = self.reset_selection()
        notebooks = []
        prev = 0
        for cell in self.iter_cells():
            if cell.num == prev:
                continue

            notebooks.append(cp[prev : cell.num].copy())

            prev = cell.num
        notebooks.append(cp[prev:].copy())
        return notebooks

    def list(self) -> list[int]:
        """
        Return the numbers of the selected cells
        :return:
        """
        return [cell.num for cell in self.list_cells()]

    def count(self) -> int:
        """
        Return the numbers of the selected cells
        :return:
        """
        return len(self)

    # == SlideShowMixin ==

    def mark_slideshow(self) -> None:
        self.raw_nb["metadata"]["celltoolbar"] = "Slideshow"

    def set_slide(self) -> None:
        self.tag_slide("slide")

    def set_skip(self) -> None:
        self.tag_slide("skip")

    def set_subslide(self) -> None:
        self.tag_slide("subslide")

    def set_fragment(self) -> None:
        self.tag_slide("fragment")

    def set_notes(self) -> None:
        self.tag_slide("notes")

    def tag_slide(self, tag: str) -> None:
        if tag not in {"-", "skip", "slide", "subslide", "fragment", "notes"}:
            raise ValueError(
                'Tag should be one of {"-", "skip", "slide", "subslide", "fragment", "notes"}'
            )
        self.update_cell_metadata("slideshow", {"slide_type": tag})

    def max_cells_per_slide(self, n_cells: int = 3, n_images: int = 1) -> None:
        from nbmanips.selector.default_selector import (
            has_output_type,
            has_slide_type,
            is_new_slide,
        )

        cells_count = 0
        img_count = 0
        for cell in self.iter_cells():
            is_image = has_output_type(cell, "image/png")
            if is_new_slide(cell):
                cells_count = 1
                img_count = 0
            elif has_slide_type(cell, {"skip", "fragment", "notes"}):
                # Don't count
                pass
            else:
                cells_count += 1
            if is_image:
                img_count += 1

            if (n_cells is not None and cells_count > n_cells) or (
                n_images is not None and img_count > n_images
            ):
                cell.update_metadata("slideshow", {"slide_type": "subslide"})
                cells_count = 1
                img_count = 1 if is_image else 0

    def auto_slide(
        self,
        max_cells_per_slide: int = 3,
        max_images_per_slide: int = 1,
        *_,
        delete_empty: bool = True,
        title_tags: str = "h1, h2",
    ) -> None:
        from nbmanips.selector.default_selector import is_new_slide

        # Delete Empty
        if delete_empty:
            self.select("is_empty").delete()

        # Each title represents
        self.select("with_css_selector", title_tags).set_slide()

        # Create a new slide only
        for cell in reversed(list(self.iter_cells())):
            if cell.num > 0 and is_new_slide(
                self[cell.num - 1].first_cell()
            ):  # previous cell is a new slide
                cell.update_metadata("slideshow", {"slide_type": "-"})

        # Set max cells per slide
        self.max_cells_per_slide(max_cells_per_slide, max_images_per_slide)

    # == ExportMixin ==

    @classmethod
    def register_exporter(
        cls,
        exporter_name: str,
        exporter: type[Exporter],
        exporter_type: str = "nbconvert",
    ) -> None:
        exporters = cls.__exporters.setdefault(exporter_type, {})
        exporters[exporter_name] = exporter

    @classmethod
    def get_exporter(
        cls, exporter_name: str, *args, exporter_type: str = "nbconvert", **kwargs
    ) -> Exporter:
        return cls.__exporters[exporter_type][exporter_name](*args, **kwargs)

    def to_json(self) -> str:
        """
        returns notebook as json string.
        """
        return json.dumps(self.raw_nb)

    def to_notebook_node(self) -> nbformat.NotebookNode:
        """
        returns notebook as an nbformat NotebookNode
        """
        return dict_to_ipynb(self.raw_nb)

    def convert(
        self,
        exporter_name: str,
        path: str,
        *args,
        exporter_type: str = "nbmanips",
        **kwargs,
    ) -> None:
        if exporter_type not in {"nbmanips", "nbconvert"}:
            raise ValueError('exporter_type should be in {"nbmanips", "nbconvert"}')
        if exporter_type == "nbconvert":
            return self.nbconvert(exporter_name, path, *args, **kwargs)

        exporter = self.get_exporter(exporter_name, exporter_type=exporter_type)

        return exporter.export(self, path, *args, **kwargs)

    def nbconvert(
        self,
        exporter_name: str,
        path: str,
        *args,
        template_name: str | None = None,
        **kwargs,
    ) -> None:
        notebook_node = self.to_notebook_node()

        if template_name is not None:
            kwargs["template_name"] = template_name

        exporter = self.get_exporter(
            exporter_name, *args, exporter_type="nbconvert", **kwargs
        )

        (body, resources) = exporter.from_notebook_node(notebook_node)

        # Exporting result
        build_directory, file_name = os.path.split(path)
        writer = nbconvert.writers.files.FilesWriter(build_directory=build_directory)

        _, ext = os.path.splitext(file_name)
        if ext:
            resources.pop("output_extension")

        writer.write(body, resources, file_name)

    def to_html(
        self,
        path: str,
        exclude_code_cell: bool = False,
        exclude_markdown: bool = False,
        exclude_raw: bool = False,
        exclude_unknown: bool = False,
        exclude_input: bool = False,
        exclude_output: bool = False,
        **kwargs,
    ) -> None:
        """
        Exports a basic HTML document.

        :param path: path to export to
        :param exclude_code_cell: exclude code cells from all templates if set to True.
        :param exclude_markdown: exclude markdown cells from all templates if set to True.
        :param exclude_raw: exclude raw cells from all templates if set to True.
        :param exclude_unknown: exclude unknown cells from all templates if set to True.
        :param exclude_input: exclude input prompts from all templates if set to True.
        :param exclude_output: exclude code cell outputs from all templates if set to True.
        :param kwargs: exclude_input_prompt, exclude_output_prompt, ...
        """
        return self.nbconvert(
            "html",
            path,
            exclude_code_cell=exclude_code_cell,
            exclude_markdown=exclude_markdown,
            exclude_raw=exclude_raw,
            exclude_unknown=exclude_unknown,
            exclude_input=exclude_input,
            exclude_output=exclude_output,
            **kwargs,
        )

    def to_py(self, path: str, **kwargs) -> None:
        """
        Exports a Python code file.
        Note that the file produced will have a shebang of '#!/usr/bin/env python'
        regardless of the actual python version used in the notebook.

        :param path: path to export to
        """
        return self.nbconvert("python", path, **kwargs)

    def to_md(
        self,
        path: str,
        exclude_code_cell: bool = False,
        exclude_markdown: bool = False,
        exclude_raw: bool = False,
        exclude_unknown: bool = False,
        exclude_input: bool = False,
        exclude_output: bool = False,
        **kwargs,
    ) -> None:
        """
        Exports to a markdown document (.md)

        :param path: path to export to
        :param exclude_code_cell: exclude code cells from all templates if set to True.
        :param exclude_markdown: exclude markdown cells from all templates if set to True.
        :param exclude_raw: exclude raw cells from all templates if set to True.
        :param exclude_unknown: exclude unknown cells from all templates if set to True.
        :param exclude_input: exclude input prompts from all templates if set to True.
        :param exclude_output: exclude code cell outputs from all templates if set to True.
        :param kwargs: exclude_input_prompt, exclude_output_prompt, ...
        """
        return self.nbconvert(
            "markdown",
            path,
            exclude_code_cell=exclude_code_cell,
            exclude_markdown=exclude_markdown,
            exclude_raw=exclude_raw,
            exclude_unknown=exclude_unknown,
            exclude_input=exclude_input,
            exclude_output=exclude_output,
            **kwargs,
        )

    def to_slides(
        self,
        path: str,
        scroll: bool = True,
        transition: str = "slide",
        theme: str = "simple",
        **kwargs,
    ) -> None:
        """
        Exports HTML slides with reveal.js

        :param path: path to export to
        :param scroll: If True, enable scrolling within each slide
        :type scroll: bool
        :param transition: Name of the reveal.js transition to use.
        :type transition: none, fade, slide, convex, concave and zoom.
        :param theme: Name of the reveal.js theme to use.
        See https://github.com/hakimel/reveal.js/tree/master/css/theme
        :type theme: beige, black, blood, league, moon, night, serif, simple, sky, solarized, white
        :param kwargs: any additional keyword arguments to nbconvert exporter
        :type kwargs: exclude_code_cell, exclude_markdown, exclude_input, exclude_output, ...
        """
        return self.nbconvert(
            "slides",
            path,
            reveal_scroll=scroll,
            reveal_transition=transition,
            reveal_theme=theme,
            **kwargs,
        )

    def to_dbc(
        self,
        path: str,
        filename: str | None = None,
        name: str | None = None,
        language: str | None = None,
        version: str = "NotebookV1",
    ) -> None:
        """
        Exports Notebook to dbc archive file

        :param path: path to export to
        :param filename: filename of the notebook inside archive (e.i. notebook.python)
        :param name: name of the notebook
        :param language: language of the notebook
        :param version: version of dbc file (default is NotebookV1)
        :return:
        """
        self.convert(
            "dbc",
            path,
            exporter_type="nbmanips",
            filename=filename,
            name=name,
            language=language,
            version=version,
        )

    def _get_pygments_lexer(self, use_pygments: bool):
        if use_pygments:
            pygments_lexer = self.metadata.get("language_info", {}).get(
                "pygments_lexer", None
            )
            pygments_lexer = pygments_lexer or self.metadata.get(
                "language_info", {}
            ).get("name", None)
            pygments_lexer = pygments_lexer or self.metadata.get("kernelspec", {}).get(
                "language", None
            )
        else:
            pygments_lexer = None

        if pygments_lexer is None:
            return pygments_lexer

        if get_lexer_by_name is None:
            raise ModuleNotFoundError(
                "You need to install pygments first.\n pip install pygments"
            )

        try:
            if pygments_lexer in {"ipython3", "python", "py", "python3", "py3"}:
                from pygments.lexers.python import PythonLexer

                return PythonLexer()

            return get_lexer_by_name(pygments_lexer)
        except pygments.util.ClassNotFound:
            return None

    def to_str(
        self,
        width: int | None = None,
        exclude_output: bool = False,
        use_pygments: bool | None = None,
        style: str = "single",
        border_color: str | None = None,
        parsers: Iterable[str] | None = None,
        parsers_config: dict[str, dict[str, Any]] | None = None,
        excluded_data_types: Iterable[str] | None = None,
        truncate: int | None = None,
    ) -> str:
        use_pygments = PYGMENTS_SUPPORTED if use_pygments is None else use_pygments
        pygments_lexer = self._get_pygments_lexer(use_pygments)

        return "\n".join(
            cell.to_str(
                width=width,
                exclude_output=exclude_output,
                use_pygments=use_pygments,
                pygments_lexer=pygments_lexer,
                style=style,
                color=border_color,
                parsers=parsers,
                parsers_config=parsers_config,
                excluded_data_types=excluded_data_types,
                truncate=truncate,
            )
            for cell in self.iter_cells()
        )

    def to_text(self, path: str, *args, **kwargs) -> None:
        """
        Exports to visual text format
        :param path: path to export to
        :param args:
        :param kwargs:
        :return:
        """
        content = self.to_str(*args, use_pygments=False, border_color=False, **kwargs)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def to_ipynb(self, path: str) -> None:
        """
        Export to ipynb file
        :param path: target path
        """
        write_ipynb(self.raw_nb, path)

    def show(
        self,
        width: int | None = None,
        exclude_output: bool = False,
        use_pygments: bool | None = None,
        style: str = "single",
        border_color: str | None = None,
        parsers: Iterable[str] | None = None,
        parsers_config: dict[str, dict[str, Any]] | None = None,
        excluded_data_types: Iterable[str] | None = None,
        truncate: int | None = None,
    ) -> None:
        """
        Show the selected cells
        :param width:
        :param style:
        :param use_pygments:
        :param border_color:
        :param exclude_output:
        :param parsers:
        :param parsers_config:
        :param excluded_data_types: output data types to exclude in the output
        :param truncate: maximum number of characters to keep. Anything beyond is truncated
        """
        str_repr = self.to_str(
            width=width,
            use_pygments=use_pygments,
            exclude_output=exclude_output,
            style=style,
            border_color=border_color,
            parsers=parsers,
            parsers_config=parsers_config,
            excluded_data_types=excluded_data_types,
            truncate=truncate,
        )
        if str_repr:
            print(str_repr)

    @classmethod
    def read_ipynb(
        cls, path: str, name: str | None = None, validate: bool = False
    ) -> Notebook:
        """
        Read ipynb file
        :param path: path to the ipynb file
        :param name: name of the Notebook
        :param validate: validate the notebook fields
        :return: Notebook object
        """
        nb = read_ipynb(path)
        nb_obj = cls(nb, name or get_ipynb_name(path), validate=validate, copy=False)

        nb_obj._original_path = path

        return nb_obj

    @classmethod
    def read_dbc(
        cls,
        path: str,
        filename: str | None = None,
        encoding: str = "utf-8",
        name: str | None = None,
        validate: bool = False,
    ) -> Notebook:
        from nbmanips.notebook.dbc import read_dbc

        dbc_name, nb = read_dbc(path, filename=filename, encoding=encoding)
        nb_obj = cls(nb, name or dbc_name, validate=validate, copy=False)

        nb_obj._original_path = path

        return nb_obj

    @classmethod
    def read_zpln(
        cls,
        path: str,
        encoding: str = "utf-8",
        name: str | None = None,
        validate: bool = False,
    ) -> Notebook:
        from nbmanips.notebook.zpln import read_zpln

        zpln_name, nb = read_zpln(path, encoding=encoding)
        nb_obj = cls(nb, name or zpln_name, validate=validate, copy=False)

        nb_obj._original_path = path

        return nb_obj

    @classmethod
    def read(
        cls, path: str, name: str | None = None, validate: bool = False, **kwargs
    ) -> Notebook:
        readers: Callable[[str, str | None, bool], Notebook] = {
            ".ipynb": cls.read_ipynb,
            ".dbc": cls.read_dbc,
            ".zpln": cls.read_zpln,
        }

        if not Path(path).exists():
            raise FileNotFoundError(f"Could not find: {path}")

        ext = Path(path).suffix.lower()
        if reader := readers.get(ext):
            return reader(path, name=name, validate=validate, **kwargs)

        for reader in readers.values():
            with suppress(Exception):
                return reader(path, name=name, validate=validate, **kwargs)

        raise ValueError("Could not determine the notebook type")

    # == NotebookMetadata ==

    @property
    def language(self) -> str | None:
        lang = self.metadata.get("kernelspec", {}).get("language", None)
        lang = lang or self.metadata.get("language_info", {}).get("name", None)
        return lang or self.metadata.get("language_info", {}).get(
            "pygments_lexer", None
        )

    def add_author(self, name: str, **kwargs) -> None:
        """
        Add author to metadata
        :param name: name of the author
        :param kwargs: any additional information about the author
        """
        if "authors" not in self.metadata:
            self.metadata["authors"] = []

        # Create author info
        author_inf = {"name": name}
        author_inf.update(kwargs)

        # add author
        self.metadata["authors"].append(author_inf)

    def set_kernelspec(
        self, argv: str, display_name: str, language: str, **kwargs
    ) -> None:
        """
        set the kernel specs.

        See https://jupyter-client.readthedocs.io/en/stable/kernels.html#kernelspecs
        for more information

        :param argv: A list of command line arguments used to start the kernel.
        :param display_name:The kernel's name as it should be displayed in the UI.
            Unlike the kernel name used in the API, this can contain arbitrary unicode characters.
        :param language: The name of the language of the kernel.
        :param kwargs: optional keyword arguments
        """
        # Create kernelspec
        kernelspec = {"argv": argv, "display_name": display_name, "language": language}
        kernelspec.update(kwargs)

        # set kernelspec
        self.metadata["kernelspec"] = kernelspec

    # == NotebookCellMetadata ==

    def add_tag(self, tag: str) -> None:
        """
        Add tag to cell metadata.
        :param tag: tag to add
        """
        for cell in self.iter_cells():
            cell.add_tag(tag)

    def remove_tag(self, tag: str) -> None:
        """
        remove tag to cell metadata.
        :param tag: tag to remove
        """
        for cell in self.iter_cells():
            cell.remove_tag(tag)

    def set_collapsed(self, value: bool = True) -> None:
        """
        Whether the cell's output container should be collapsed
        :param value: boolean
        """
        self.update_cell_metadata("collapsed", value)

    def set_scrolled(self, value: bool | str = False) -> None:
        """
        Whether the cell's output is scrolled, unscrolled, or autoscrolled
        :param value: bool or 'auto'
        """
        self.update_cell_metadata("scrolled", value)

    def set_deletable(self, value: bool = True) -> None:
        """
        If False, prevent deletion of the cell
        :param value: boolean
        """
        self.update_cell_metadata("deletable", value)

    def set_editable(self, value: bool = True) -> None:
        """
        If False, prevent editing of the cell (by definition, this also prevents deleting the cell)
        :param value: boolean
        """
        self.update_cell_metadata("editable", value)

    def set_format(self, value: str) -> None:
        """
        The mime-type of a Raw NBConvert Cell
        :param value: 'mime/type'
        """
        self.update_cell_metadata("format", value)

    def set_name(self, value: str) -> None:
        """
        A name for the cell. Should be unique across the notebook.
        Uniqueness must be verified outside of the json schema.
        :param value: name of the cell
        """
        # TODO: check name is unique
        self.update_cell_metadata("name", value)

    def hide_source(self, value: bool = True) -> None:
        """
        Whether the cell's source should be shown
        :param value: boolean
        """
        self.update_cell_metadata("jupyter", {"source_hidden": value})

    def hide_output(self, value: bool = True) -> None:
        """
        Whether the cell's outputs should be shown.
        :param value: boolean
        """
        self.update_cell_metadata("jupyter", {"outputs_hidden": value})

    def burn_attachments(
        self, assets_path: str | None = None, html: bool = True
    ) -> None:
        import re
        from functools import partial

        from nbmanips.cell.cell_utils import (
            HTML_IMG_EXPRESSION,
            HTML_IMG_REGEX,
            MD_IMG_EXPRESSION,
            MD_IMG_REGEX,
            burn_attachment,
            get_assets_path,
        )

        assets_path = get_assets_path(self, assets_path)
        compiled_md_regex = re.compile(MD_IMG_REGEX)
        compiled_html_regex = re.compile(HTML_IMG_REGEX)

        for cell in self.select("markdown_cells").iter_cells():
            # replace markdown
            rep_func = partial(
                burn_attachment,
                cell=cell,
                assets_path=assets_path,
                expr=MD_IMG_EXPRESSION,
            )
            cell.source = compiled_md_regex.sub(rep_func, cell.get_source())

            if not html:
                continue

            # replace html
            rep_func = partial(
                burn_attachment,
                cell=cell,
                assets_path=assets_path,
                expr=HTML_IMG_EXPRESSION,
            )
            cell.source = compiled_html_regex.sub(rep_func, cell.get_source())

    # == ContentAnalysisMixin ==

    @property
    def toc(self) -> list[tuple[int, str, int]]:
        markdown_cells = self.select("is_markdown")

        toc = []
        indentation_levels = []
        for cell in markdown_cells.iter_cells():
            for element in cell.soup.select("h1, h2, h3, h4, h5, h6"):
                indentation_level = int(element.name[-1]) - 1
                indentation_levels.append(indentation_level)
                toc.append((indentation_level, element.text, cell.num))

        return toc

    def ptoc(self, width: int | None = None, index: bool = False) -> str:
        import textwrap

        toc = self.toc

        if not toc:
            return ""

        min_indentation = min(ind_level for ind_level, _, _ in toc)

        indented_toc = [
            ("  " * (ind - min_indentation) + title, cell_num)
            for ind, title, cell_num in toc
        ]

        if width is None:
            import shutil

            max_width = shutil.get_terminal_size().columns
            max_length = max(len(x) for x, _ in indented_toc) + 7
            width = min(max_width, max_length)
        width -= 7

        wrapped_toc = [(textwrap.wrap(title, width), n) for title, n in indented_toc]

        printable_toc = []
        for title, cell_num in wrapped_toc:
            if index:
                title[0] = title[0] + " " * (width - len(title[0])) + f"  [{cell_num}]"
            printable_toc.extend(title)

        return "\n".join(printable_toc)

    def show_toc(self, width: int | None = None, index: bool = True) -> None:
        print(self.ptoc(width, index))

    def add_toc(self, pos: int = 0, bullets: bool = False) -> None:
        from nbmanips.cell import Cell

        toc = self.toc

        if not toc:
            raise ValueError("Could not build Table of contents. No headers found.")

        min_indentation = min(ind_level for ind_level, _, _ in toc)

        numbered_toc = []
        stack = [0, 0, 0, 0, 0, 0]
        for ind, title, _ in toc:
            for i in range(ind + 1, len(stack)):
                stack[i] = 0
            stack[ind] += 1
            numbered_toc.append((stack[ind], ind, title))

        indented_toc = [
            "  " * (ind - min_indentation)
            + ("- " if bullets else f"{num}. ")
            + f"[{title}](#{title.replace(' ', '-')})\n"
            for num, ind, title in numbered_toc
        ]

        toc_cell = Cell(
            {"cell_type": "markdown", "source": "\n".join(indented_toc), "metadata": {}}
        )

        self.add_cell(toc_cell, pos)

    # == Notebook ==

    def search(
        self, text: str, case: bool = False, output: bool = False, regex: bool = False
    ) -> int | None:
        """
        Return the number of the first cell containing the given text
        :param text: a string to find in cell
        :param case: True if the search is case-sensitive
        :type case: default False
        :param output: True if you want the search in the output of the cell too
        :type output: default False
        :param regex: boolean whether to use regex or not
        :return:
        """

        if not regex:
            return self.select("contains", text=text, case=case, output=output).first()

        compiled_regex = _get_regex(text, case=case, regex=regex)
        return self.select("has_match", compiled_regex, output=output).first()

    def search_all(
        self, text: str, case: bool = False, output: bool = False, regex: bool = False
    ) -> list[int]:
        """
        Return the numbers of the cells containing the given text

        :param text: a string to find in cell
        :param case: True if the search is case-sensitive
        :type case: default False
        :param output: True if you want the search in the output of the cell too
        :type output: default False
        :param regex: boolean whether to use regex or not
        :return:
        """

        if not regex:
            return self.select("contains", text=text, case=case, output=output).list()

        compiled_regex = _get_regex(text, case=case, regex=regex)
        return self.select("has_match", compiled_regex, output=output).list()

    def replace(
        self,
        old: str,
        new: str,
        count: int | None = None,
        case: bool = True,
        regex: bool = False,
    ) -> None:
        """
        Replace matching text in the selected cells

        :param old: a string to replace in cell
        :param new: the replacement string
        :param count:
        :param case: True if the search is case-sensitive
        :type case: default True
        :param regex: boolean whether to use regex or not
        """

        compiled_regex = _get_regex(old, case=case, regex=regex)
        selection = self.select("has_match", compiled_regex)
        for n_cells, cell in enumerate(selection.iter_cells(), start=1):
            cell.source = compiled_regex.sub(new, cell.get_source())
            if count is not None and n_cells >= count:
                break


class IPYNB(Notebook):
    def __new__(cls, path: str, name: str | None = None) -> Notebook:
        return Notebook.read_ipynb(path, name)


class DBC(Notebook):
    def __new__(
        cls,
        path: str,
        filename: str | None = None,
        encoding: str = "utf-8",
        name: str | None = None,
    ) -> Notebook:
        return Notebook.read_dbc(path, filename=filename, encoding=encoding, name=name)


class ZPLN(Notebook):
    def __new__(
        cls, path: str, name: str | None = None, encoding: str = "utf-8"
    ) -> Notebook:
        return Notebook.read_zpln(path, encoding=encoding, name=name)
