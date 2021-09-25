import shutil
import uuid
import re
from copy import deepcopy
from typing import Any, Optional, Union

try:
    import pygments
except ImportError:
    pygments = None

from nbmanips.cell_utils import printable_cell
from nbmanips.cell_output import CellOutput
from nbmanips.utils import total_size


class Cell:
    cell_type = None
    _cell_types = None

    def __init__(self, content, num=None):
        self.cell = content
        self._num = num
        assert self.type == self.cell_type

    def __getitem__(self, key):
        return self.cell[key]

    def __setitem__(self, key, value):
        self.cell[key] = value

    @property
    def type(self):
        return self.cell['cell_type']

    @property
    def id(self):
        return self.cell.get('id', None)

    @id.setter
    def id(self, new_id):
        self.cell['id'] = new_id

    @property
    def num(self):
        return self._num

    @property
    def metadata(self):
        return self.cell['metadata']

    @property
    def source(self):
        return self.get_source().strip()

    @property
    def output(self):
        return self.get_output(text=True, readable=True).strip()

    @property
    def outputs(self):
        return map(CellOutput.new, self.cell.get('outputs', []))

    def get_copy(self, new_id=None):
        cell = self.__class__(deepcopy(self.cell), None)
        if new_id is not None:
            cell.id = new_id
        return cell

    def get_output(self, text=True, readable=True, exclude_data_types=None, exclude_errors=True, **kwargs):
        """
        Tries its best to return a readable output from cell

        :param exclude_data_types:
        :param exclude_errors:
        :param text:
        :param readable:
        :return:
        """

        outputs = []
        for cell_output in self.outputs:
            outputs.append(cell_output.to_str(readable, exclude_data_types, **kwargs))

        if text:
            return '\n'.join(outputs)
        return outputs

    def get_source(self, text=True):
        source = self.cell['source']

        if text and not isinstance(source, str):
            return '\n'.join(source)
        return source

    def set_source(self, content, text=False):
        if text:
            content = content.split('\n')
        self.cell['source'] = content

    def contains(self, text, case=True, output=False, regex=False, flags=0):
        search_target = self.source
        if output:
            search_target += ('\n' + self.output)

        if not regex:
            text = re.escape(text)

        if case is False:
            flags = flags | re.IGNORECASE
        else:
            flags = flags & ~re.IGNORECASE
        return bool(re.search(text, search_target, flags=flags))

    def erase_output(self, output_types: Optional[Union[str, set]] = None):
        """
        erase output of cells that have a given output_type

        :param output_types: Output Type(MIME type) to delete: text/plain, text/html, image/png, ...
        :type output_types: set or str or None to delete all output
        """
        outputs = list(self.outputs)
        if len(outputs) == 0:
            return

        if output_types is None:
            self['outputs'] = []
            return
        elif isinstance(output_types, str):
            output_types = {output_types}
        else:
            output_types = set(output_types)

        new_outputs = []
        for cell_output in outputs:
            new_output = cell_output.erase_output(output_types)
            if new_output is not None:
                new_outputs.append(new_output)

        self['outputs'] = new_outputs

    def has_output_type(self, output_types: set):
        """
        Select cells that have a given output_type

        :param output_types: Output Types(MIME type) to select: text/plain, text/html, image/png, ...
        :type output_types: set
        :return: a bool object (True if cell should be selected)
        """
        return any(cell_output.has_output_type(output_types) for cell_output in self.outputs)

    def byte_size(self, output_types: Optional[set] = None, ignore_source=False):
        """
        returns the byte size of the cell.

        :param output_types: Output Types(MIME type) to select: text/plain, text/html, image/png, ...
        :type output_types: set
        :param ignore_source: True if you want to get the size of the output only
        :return: a bool object (True if cell should be selected)
        """
        size = 0 if ignore_source else total_size(self['source'])
        size += sum([CellOutput.new(output).byte_size(output_types) for output in self['outputs']])
        return size

    def to_str(self, width=None, style='single', use_pygments=None, pygments_lexer=None, color=None,
               exclude_output=False, img_color=None, img_width=None):
        return self.source

    def show(self):
        print(self)

    def __repr__(self):
        return f"<Cell {self.num}>" if self.num else "<Cell>"

    def __str__(self):
        return self.to_str(width=None, style='single', color=None, img_color=None)

    # metadata
    def update_metadata(self, key: str, value: Any):
        """
        Add metadata to the selected cells
        :param key: metadata key
        :param value: metadata value
        """
        if 'metadata' not in self.cell:
            self.cell['metadata'] = {}

        if key in self.cell['metadata'] and isinstance(self.cell['metadata'][key], dict):
            self.metadata[key].update(value)
        else:
            self.metadata[key] = value

    def add_tag(self, tag: str):
        """
        Add tag to cell metadata.
        :param tag: tag to add
        """
        if 'metadata' not in self.cell:
            self.cell['metadata'] = {}

        if 'tags' not in self.metadata:
            self.metadata['tags'] = []

        if tag in self.metadata['tags']:
            return

        self.metadata['tags'].append(tag)

    def remove_tag(self, tag: str):
        """
        remove tag to cell metadata.
        :param tag: tag to remove
        """

        if 'metadata' not in self.cell or 'tags' not in self.metadata:
            return

        while tag in self.metadata['tags']:
            self.metadata['tags'].remove(tag)

    @staticmethod
    def generate_id_candidate():
        return uuid.uuid4().hex[:8]

    @classmethod
    def new(cls, content, num=None, build_cell_types=False):
        if build_cell_types or cls._cell_types is None:
            cls._cell_types = cls._get_cell_types()

        cell_class = cls._cell_types[content['cell_type']]
        return cell_class(content, num)

    @classmethod
    def _get_cell_types(cls):
        cell_types = {}
        for cell_class in cls.__subclasses__():
            if cell_class.cell_type is None:
                cell_types.update(cell_class._get_cell_types())
            else:
                cell_types[cell_class.cell_type] = cell_class
        return cell_types


class CodeCell(Cell):
    cell_type = "code"

    def to_str(self, width=None, style='single', use_pygments=None, pygments_lexer=None, color=None,
               exclude_output=False, img_color=None, img_width=None):
        sources = [printable_cell(self.source, width=width, style=style, color=color, pygments_lexer=pygments_lexer)]

        if not exclude_output:
            img_color = bool(color) if img_color is None else img_color
            width = width or (shutil.get_terminal_size().columns - 1)
            img_width = img_width if img_width else int(width * 0.7)
            output = self.get_output(text=True, readable=True, colorful=img_color, width=img_width).strip()
            if output:
                sources.append(output)

        return '\n'.join(sources)


class MarkdownCell(Cell):
    cell_type = "markdown"

    def to_str(self, width=None, style='single', use_pygments=None, pygments_lexer=None, color=None, exclude_output=False, img_color=None,
               img_width=None):
        use_pygments = pygments is not None if use_pygments is None else use_pygments

        if use_pygments:
            if pygments is None:
                raise ModuleNotFoundError("You need to install pygments first.\n pip install nbmanips[pygments]")
            formatter = getattr(pygments.formatters, 'TerminalFormatter')
            lexer = getattr(pygments.lexers, 'MarkdownLexer')
            return pygments.highlight(self.source, lexer(), formatter())[:-1]
        else:
            return self.source


class RawCell(Cell):
    cell_type = "raw"

