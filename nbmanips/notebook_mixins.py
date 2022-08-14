import json
import os
import shutil
import textwrap
from copy import deepcopy
from pathlib import Path
from typing import Any, Union

try:
    import nbconvert
except ImportError:
    nbconvert = None

from nbmanips.cell_utils import PYGMENTS_SUPPORTED
from nbmanips.notebook_base import NotebookBase
from nbmanips.selector import has_output_type, has_slide_type, is_new_slide
from nbmanips.utils import (
    dict_to_ipynb,
    get_ipynb_name,
    read_dbc,
    read_ipynb,
    read_zpln,
    write_ipynb,
)

try:
    import pygments.util
    from pygments.lexers import get_lexer_by_name
except ImportError:
    pygments = None
    get_lexer_by_name = None


class ClassicNotebook(NotebookBase):
    def update_cell_metadata(self, key: str, value: Any):
        """
        Add metadata to the selected cells
        :param key: metadata key
        :param value: metadata value
        """
        for cell in self.iter_cells():
            value = deepcopy(value)
            cell.update_metadata(key, value)

    def erase(self):
        """
        Erase the content of the selected cells
        """
        for cell in self.iter_cells():
            cell.set_source([])

    def erase_output(self, output_types=None):
        """
        Erase the output content of the selected cells
        """
        for cell in self.iter_cells():
            cell.erase_output(output_types)

    def delete(self):
        """
        Delete the selected cells
        """
        self.raw_nb['cells'] = [cell.cell for cell in self.iter_cells(neg=True)]

    def keep(self):
        """
        Delete all the non-selected cells
        """
        self.raw_nb['cells'] = [cell.cell for cell in self.iter_cells()]

    def first(self):
        """
        Return the number of the first selected cell
        :return:
        """
        for cell in self.iter_cells():
            return cell.num

    def last(self):
        """
        Return the number of the last selected cell
        :return:
        """
        for cell in reversed(list(self.iter_cells())):
            return cell.num

    def copy(self, selection=True, crop=True):
        """
        Copy the notebook instance

        :param selection: keep selection
        :param crop: crop on selection
        :return: a new copy of the notebook
        """
        cp = self.__class__(self.raw_nb, self.name, validate=False)
        if selection:
            cp._selector = self._selector
            if crop:
                cp.keep()
                cp = cp.reset_selection()
        return cp

    def split(self, *args):
        """
        Split the notebook based passed selectors (typically cell indexes)

        :param args:
        :return:
        """
        return self.copy().select(args, type='or').split_on_selection()

    def split_on_selection(self):
        """
        Split the notebook based on the selected cells
        :return:
        """
        cp = self.reset_selection()
        notebooks = []
        prev = 0
        for cell in list(self.iter_cells()):
            if cell.num == prev:
                continue

            notebooks.append(cp[prev : cell.num].copy())

            prev = cell.num
        notebooks.append(cp[prev:].copy())
        return notebooks

    def list(self):
        """
        Return the numbers of the selected cells
        :return:
        """
        return [cell.num for cell in self.list_cells()]

    def count(self):
        """
        Return the numbers of the selected cells
        :return:
        """
        return len(self.list())


class SlideShowMixin(ClassicNotebook):
    def mark_slideshow(self):
        self.raw_nb['metadata']['celltoolbar'] = 'Slideshow'

    def set_slide(self):
        self.tag_slide('slide')

    def set_skip(self):
        self.tag_slide('skip')

    def set_subslide(self):
        self.tag_slide('subslide')

    def set_fragment(self):
        self.tag_slide('fragment')

    def set_notes(self):
        self.tag_slide('notes')

    def tag_slide(self, tag):
        assert tag in {'-', 'skip', 'slide', 'subslide', 'fragment', 'notes'}
        self.update_cell_metadata('slideshow', {'slide_type': tag})

    def max_cells_per_slide(self, n_cells=3, n_images=1):
        cells_count = 0
        img_count = 0
        for cell in self.iter_cells():
            is_image = has_output_type(cell, 'image/png')
            if is_new_slide(cell):
                cells_count = 1
                img_count = 0
            elif has_slide_type(cell, {'skip', 'fragment', 'notes'}):
                # Don't count
                pass
            else:
                cells_count += 1
            if is_image:
                img_count += 1

            if (n_cells is not None and cells_count > n_cells) or (
                n_images is not None and img_count > n_images
            ):
                cell.update_metadata('slideshow', {'slide_type': 'subslide'})
                cells_count = 1
                img_count = 1 if is_image else 0

    def auto_slide(
        self,
        max_cells_per_slide=3,
        max_images_per_slide=1,
        *_,
        delete_empty=True,
        title_tags='h1, h2',
    ):
        # Delete Empty
        if delete_empty:
            self.select('is_empty').delete()

        # Each title represents
        self.select('has_html_tag', title_tags).set_slide()

        # Create a new slide only
        for cell in reversed(list(self.iter_cells())):
            if cell.num > 0 and is_new_slide(
                self[cell.num - 1].first_cell()
            ):  # previous cell is a new slide
                cell.update_metadata('slideshow', {'slide_type': '-'})

        # Set max cells per slide
        self.max_cells_per_slide(max_cells_per_slide, max_images_per_slide)


class ExportMixin(NotebookBase):
    __exporters = {
        'nbconvert': {
            'html': nbconvert.HTMLExporter,
            'slides': nbconvert.SlidesExporter,
            'python': nbconvert.PythonExporter,
            'markdown': nbconvert.MarkdownExporter,
            'script': nbconvert.ScriptExporter,
        }
    }

    @classmethod
    def register_exporter(cls, exporter_name: str, exporter, exporter_type='nbconvert'):
        exporters = cls.__exporters.setdefault(exporter_type, {})
        exporters[exporter_name] = exporter

    @classmethod
    def get_exporter(cls, exporter_name, *args, exporter_type='nbconvert', **kwargs):
        return cls.__exporters[exporter_type][exporter_name](*args, **kwargs)

    def to_json(self):
        """
        returns notebook as json string.
        """
        return json.dumps(self.raw_nb)

    def to_notebook_node(self):
        """
        returns notebook as an nbformat NotebookNode
        """
        return dict_to_ipynb(self.raw_nb)

    def convert(self, exporter_name, path, *args, exporter_type='nbmanips', **kwargs):
        assert exporter_type in {'nbmanips', 'nbconvert'}
        if exporter_type == 'nbconvert':
            return self.nbconvert(exporter_name, path, *args, **kwargs)

        exporter = self.get_exporter(exporter_name, exporter_type=exporter_type)

        return exporter.export(self, path, *args, **kwargs)

    def nbconvert(self, exporter_name, path, *args, template_name=None, **kwargs):
        notebook_node = self.to_notebook_node()

        if template_name is not None:
            kwargs['template_name'] = template_name

        exporter = self.get_exporter(
            exporter_name, *args, exporter_type='nbconvert', **kwargs
        )

        (body, resources) = exporter.from_notebook_node(notebook_node)

        # Exporting result
        build_directory, file_name = os.path.split(path)
        writer = nbconvert.writers.files.FilesWriter(build_directory=build_directory)

        _, ext = os.path.splitext(file_name)
        if ext:
            resources.pop('output_extension')

        writer.write(body, resources, file_name)

    def to_html(
        self,
        path,
        exclude_code_cell=False,
        exclude_markdown=False,
        exclude_raw=False,
        exclude_unknown=False,
        exclude_input=False,
        exclude_output=False,
        **kwargs,
    ):
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
            'html',
            path,
            exclude_code_cell=exclude_code_cell,
            exclude_markdown=exclude_markdown,
            exclude_raw=exclude_raw,
            exclude_unknown=exclude_unknown,
            exclude_input=exclude_input,
            exclude_output=exclude_output,
            **kwargs,
        )

    def to_py(self, path, **kwargs):
        """
        Exports a Python code file.
        Note that the file produced will have a shebang of '#!/usr/bin/env python'
        regardless of the actual python version used in the notebook.

        :param path: path to export to
        """
        return self.nbconvert('python', path, **kwargs)

    def to_md(
        self,
        path,
        exclude_code_cell=False,
        exclude_markdown=False,
        exclude_raw=False,
        exclude_unknown=False,
        exclude_input=False,
        exclude_output=False,
        **kwargs,
    ):
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
            'markdown',
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
        self, path, scroll=True, transition='slide', theme='simple', **kwargs
    ):
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
            'slides',
            path,
            reveal_scroll=scroll,
            reveal_transition=transition,
            reveal_theme=theme,
            **kwargs,
        )

    def to_dbc(
        self, path, filename=None, name=None, language=None, version='NotebookV1'
    ):
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
            'dbc',
            path,
            exporter_type='nbmanips',
            filename=filename,
            name=name,
            language=language,
            version=version,
        )

    def _get_pygments_lexer(self, use_pygments):
        if use_pygments:
            pygments_lexer = self.metadata.get('language_info', {}).get(
                'pygments_lexer', None
            )
            pygments_lexer = pygments_lexer or self.metadata.get(
                'language_info', {}
            ).get('name', None)
            pygments_lexer = pygments_lexer or self.metadata.get('kernelspec', {}).get(
                'language', None
            )
        else:
            pygments_lexer = None

        if pygments_lexer is None:
            return pygments_lexer

        if get_lexer_by_name is None:
            raise ModuleNotFoundError(
                'You need to install pygments first.\n pip install pygments'
            )

        try:
            return get_lexer_by_name(pygments_lexer)
        except pygments.util.ClassNotFound:
            return None

    def to_str(
        self,
        width=None,
        exclude_output=False,
        use_pygments=None,
        style='single',
        border_color=None,
        parsers=None,
        parsers_config=None,
        excluded_data_types=None,
        truncate=None,
    ):
        use_pygments = PYGMENTS_SUPPORTED if use_pygments is None else use_pygments
        pygments_lexer = self._get_pygments_lexer(use_pygments)

        return '\n'.join(
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

    def to_text(self, path, *args, **kwargs):
        """
        Exports to visual text format
        :param path: path to export to
        :param args:
        :param kwargs:
        :return:
        """
        content = self.to_str(*args, use_pygments=False, border_color=False, **kwargs)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def to_ipynb(self, path):
        """
        Export to ipynb file
        :param path: target path
        """
        write_ipynb(self.raw_nb, path)

    def show(
        self,
        width=None,
        exclude_output=False,
        use_pygments=None,
        style='single',
        border_color=None,
        parsers=None,
        parsers_config=None,
        excluded_data_types=None,
        truncate=None,
    ):
        """
        Show the selected cells
        :param width:
        :param style:
        :param use_pygments:
        :param border_color:
        :param exclude_output:
        :param parsers:
        :param parsers_config:
        :param excluded_data_types:
        """
        print(
            self.to_str(
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
        )

    @classmethod
    def read_ipynb(cls, path, name=None):
        """
        Read ipynb file
        :param path: path to the ipynb file
        :param name: name of the Notebook
        :return: Notebook object
        """
        nb = read_ipynb(path)
        nb = cls(nb, name or get_ipynb_name(path), validate=False)

        nb._original_path = path

        return nb

    @classmethod
    def read_dbc(cls, path, filename=None, encoding='utf-8', name=None):
        dbc_name, nb = read_dbc(path, filename=filename, encoding=encoding)
        nb = cls(nb, name or dbc_name, validate=False)

        nb._original_path = path

        return nb

    @classmethod
    def read_zpln(cls, path, encoding='utf-8', name=None):
        zpln_name, nb = read_zpln(path, encoding=encoding)
        nb = cls(nb, name or zpln_name, validate=False)

        nb._original_path = path

        return nb

    @classmethod
    def read(cls, path, name=None, **kwargs):
        readers = {
            '.ipynb': cls.read_ipynb,
            '.dbc': cls.read_dbc,
            '.zpln': cls.read_zpln,
        }

        if not Path(path).exists():
            raise FileNotFoundError(f'Could not find: {path}')

        ext = Path(path).suffix.lower()
        reader = readers.get(ext, None)
        if reader:
            return reader(path, name=name, **kwargs)

        for reader in readers.values():
            try:
                return reader(path, name=name, **kwargs)
            except Exception:
                continue

        raise ValueError('Could not determine the notebook type')


class NotebookMetadata(NotebookBase):
    @property
    def language(self):
        lang = self.metadata.get('kernelspec', {}).get('language', None)
        lang = lang or self.metadata.get('language_info', {}).get('name', None)
        return lang or self.metadata.get('language_info', {}).get(
            'pygments_lexer', None
        )

    def add_author(self, name, **kwargs):
        """
        Add author to metadata
        :param name: name of the author
        :param kwargs: any additional information about the author
        """
        if 'authors' not in self.metadata:
            self.metadata['authors'] = []

        # Create author info
        author_inf = {'name': name}
        author_inf.update(kwargs)

        # add author
        self.metadata['authors'].append(author_inf)

    def set_kernelspec(self, argv, display_name, language, **kwargs):
        """
        set the kernel specs.

        See https://jupyter-client.readthedocs.io/en/stable/kernels.html#kernelspecs
        for more information

        :param argv: A list of command line arguments used to start the kernel.
        :param display_name:The kernel’s name as it should be displayed in the UI.
            Unlike the kernel name used in the API, this can contain arbitrary unicode characters.
        :param language: The name of the language of the kernel.
        :param kwargs: optional keyword arguments
        """
        # Create kernelspec
        kernelspec = {'argv': argv, 'display_name': display_name, 'language': language}
        kernelspec.update(kwargs)

        # set kernelspec
        self.metadata['kernelspec'] = kernelspec


class NotebookCellMetadata(ClassicNotebook):
    def add_tag(self, tag: str):
        """
        Add tag to cell metadata.
        :param tag: tag to add
        """
        for cell in self.iter_cells():
            cell.add_tag(tag)

    def remove_tag(self, tag: str):
        """
        remove tag to cell metadata.
        :param tag: tag to remove
        """
        for cell in self.iter_cells():
            cell.remove_tag(tag)

    def set_collapsed(self, value: bool = True):
        """
        Whether the cell’s output container should be collapsed
        :param value: boolean
        """
        self.update_cell_metadata('collapsed', value)

    def set_scrolled(self, value: Union[bool, str] = False):
        """
        Whether the cell’s output is scrolled, unscrolled, or autoscrolled
        :param value: bool or ‘auto’
        """
        self.update_cell_metadata('scrolled', value)

    def set_deletable(self, value: bool = True):
        """
        If False, prevent deletion of the cell
        :param value: boolean
        """
        self.update_cell_metadata('deletable', value)

    def set_editable(self, value: bool = True):
        """
        If False, prevent editing of the cell (by definition, this also prevents deleting the cell)
        :param value: boolean
        """
        self.update_cell_metadata('editable', value)

    def set_format(self, value: str):
        """
        The mime-type of a Raw NBConvert Cell
        :param value: ‘mime/type’
        """
        self.update_cell_metadata('format', value)

    def set_name(self, value: str):
        """
        A name for the cell. Should be unique across the notebook.
        Uniqueness must be verified outside of the json schema.
        :param value: name of the cell
        """
        # TODO: check name is unique
        self.update_cell_metadata('name', value)

    def hide_source(self, value=True):
        """
        Whether the cell’s source should be shown
        :param value: boolean
        """
        self.update_cell_metadata('jupyter', {'source_hidden': value})

    def hide_output(self, value=True):
        """
        Whether the cell’s outputs should be shown
        :param value: boolean
        """
        self.update_cell_metadata('jupyter', {'outputs_hidden': value})

    def burn_attachments(self, assets_path=None, html=True):
        import re
        from functools import partial

        from nbmanips.utils import (
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

        for cell in self.select('markdown_cells').iter_cells():
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


class ContentAnalysisMixin(NotebookBase):
    @property
    def toc(self):
        markdown_cells = self.select('is_markdown')

        toc = []
        indentation_levels = []
        for cell in markdown_cells.iter_cells():
            for element in cell.soup.select('h1, h2, h3, h4, h5, h6'):
                indentation_level = int(element.name[-1]) - 1
                indentation_levels.append(indentation_level)
                toc.append((indentation_level, element.text, cell.num))

        return toc

    def ptoc(self, width=None, index=False):
        toc = self.toc

        if not toc:
            return ''

        min_indentation = min(ind_level for ind_level, _, _ in toc)

        indented_toc = [
            ('  ' * (ind - min_indentation) + title, cell_num)
            for ind, title, cell_num in toc
        ]

        if width is None:
            max_width = shutil.get_terminal_size().columns
            max_length = max(len(x) for x, _ in indented_toc) + 7
            width = min(max_width, max_length)
        width -= 7

        wrapped_toc = [(textwrap.wrap(title, width), n) for title, n in indented_toc]

        printable_toc = []
        for title, cell_num in wrapped_toc:
            if index:
                title[0] = title[0] + ' ' * (width - len(title[0])) + f'  [{cell_num}]'
            printable_toc.extend(title)

        return '\n'.join(printable_toc)

    def show_toc(self, width=None, index=True):
        print(self.ptoc(width, index))

    def add_toc(self, pos=0, bullets=False):
        from nbmanips.cell import Cell

        toc = self.toc

        if not toc:
            raise ValueError('Could not build Table of contents. No headers found.')

        min_indentation = min(ind_level for ind_level, _, _ in toc)

        numbered_toc = []
        stack = [0, 0, 0, 0, 0, 0]
        for ind, title, _ in toc:
            for i in range(ind + 1, len(stack)):
                stack[i] = 0
            stack[ind] += 1
            numbered_toc.append((stack[ind], ind, title))

        indented_toc = [
            '  ' * (ind - min_indentation)
            + ('- ' if bullets else f'{num}. ')
            + f"[{title}](#{title.replace(' ', '-')})\n"
            for num, ind, title in numbered_toc
        ]

        toc_cell = Cell(
            {'cell_type': 'markdown', 'source': '\n'.join(indented_toc), 'metadata': {}}
        )

        self.add_cell(toc_cell, pos)
