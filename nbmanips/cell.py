import base64
import re
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import pygments
    from pygments.lexers import get_lexer_by_name

    _MARKDOWN_LEXER = get_lexer_by_name('md')
except ImportError:
    pygments = None
    get_lexer_by_name = None

from bs4 import BeautifulSoup
from nbconvert.filters.markdown_mistune import IPythonRenderer, MarkdownWithMath

from nbmanips.cell_output import CellOutput
from nbmanips.cell_utils import FORMATTER, get_mime_type, monochrome, printable_cell
from nbmanips.utils import total_size


class Cell:
    _cell_types: Dict[str, type] = {}

    def __init__(self, content, num=None):
        self.cell = content
        self._num = num

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

    @source.setter
    def source(self, source: str):
        self.set_source(source)

    @property
    def output(self):
        return self.get_output(text=True).strip()

    @property
    def outputs(self):
        return map(CellOutput, self.cell.get('outputs', []))

    def get_copy(self, new_id=None):
        cell = self.__class__(deepcopy(self.cell), None)
        if new_id is not None:
            cell.id = new_id
        return cell

    def get_output(
        self, text=True, parsers=None, parsers_config=None, excluded_data_types=None
    ):
        """
        Tries its best to return a readable output from cell

        :param text:
        :param parsers: parsers to use
        :param parsers_config: custom config for parsers
        :param excluded_data_types: data types to exclude
        :return:
        """

        outputs = []
        for cell_output in self.outputs:
            text_output = cell_output.to_str(
                parsers, parsers_config, excluded_data_types
            )
            outputs.append(text_output)

        if text:
            return '\n'.join(outputs)
        return outputs

    def get_source(self, text=True):
        source = self.cell['source']

        if text and not isinstance(source, str):
            return ''.join(source)
        return source

    def set_source(self, content: Union[str, List[str]], text=False):
        if text:
            assert isinstance(content, str), 'content is not of type str if text=True'
            lines = content.split('\n')
            content = [
                f'{line}\n' if i != len(lines) else line for i, line in enumerate(lines)
            ]
        self.cell['source'] = content

    def contains(self, text, case=True, output=False, regex=False, flags=0):
        search_target = self.source
        if output:
            search_target += '\n' + self.output

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

        :param output_types: Output Types(MIME type) to select: text/plain, image/png, ...
        :type output_types: set
        :return: a bool object (True if cell should be selected)
        """
        return any(
            cell_output.has_output_type(output_types) for cell_output in self.outputs
        )

    def byte_size(self, output_types: Optional[set] = None, ignore_source=False):
        """
        returns the byte size of the cell.

        :param output_types: Output Types(MIME type) to select: text/plain, image/png, ...
        :type output_types: set
        :param ignore_source: True if you want to get the size of the output only
        :return: a bool object (True if cell should be selected)
        """
        size = 0 if ignore_source else total_size(self['source'])
        size += sum(cell_output.byte_size(output_types) for cell_output in self.outputs)
        return size

    def to_str(self, width=None, *args, **kwargs):
        return self.source

    def show(self):
        print(self)

    def __repr__(self):
        return f'<Cell {self.num}>' if self.num else '<Cell>'

    def __str__(self):
        return self.to_str(width=None, style='single', color=None)

    # metadata
    def update_metadata(self, key: str, value: Any):
        """
        Add metadata to the selected cells
        :param key: metadata key
        :param value: metadata value
        """
        if 'metadata' not in self.cell:
            self.cell['metadata'] = {}

        if key in self.cell['metadata'] and isinstance(
            self.cell['metadata'][key], dict
        ):
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

    def __new__(cls, content, *args, **kwargs):
        cell_type = content['cell_type']
        cell_class = cls._cell_types[cell_type]
        obj = super().__new__(cell_class)
        cell_class.__init__(obj, content, *args, **kwargs)
        return obj

    def __init_subclass__(cls, cell_type=None, **kwargs):
        super().__init_subclass__(**kwargs)
        if cell_type:
            cls._cell_types[cell_type] = cls


class CodeCell(Cell, cell_type='code'):
    def to_str(
        self,
        width=None,
        style='single',
        use_pygments=None,
        pygments_lexer=None,
        color=None,
        exclude_output=False,
        parsers=None,
        parsers_config=None,
        excluded_data_types=None,
        truncate=None,
    ):
        sources = [
            printable_cell(
                self.source,
                width=width,
                style=style,
                color=color,
                pygments_lexer=pygments_lexer,
            )
        ]

        if not exclude_output:
            output = self.get_output(
                text=True,
                parsers=parsers,
                parsers_config=parsers_config,
                excluded_data_types=excluded_data_types,
            ).strip()
            monochrome_output = monochrome(output)
            if truncate is not None and len(monochrome_output) > truncate >= 0:
                output = monochrome_output[:truncate] + ' [...]'
            if output:
                sources.append(output)

        return '\n'.join(sources)


class MarkdownCell(Cell, cell_type='markdown'):
    _bs4_parser = 'lxml'

    def to_str(
        self,
        width=None,
        style='single',
        use_pygments=None,
        pygments_lexer=None,
        color=None,
        **kwargs,
    ):
        use_pygments = pygments is not None if use_pygments is None else use_pygments

        if use_pygments:
            if pygments is None:
                raise ModuleNotFoundError(
                    'You need to install pygments first.\n pip install pygments'
                )
            return pygments.highlight(self.source, _MARKDOWN_LEXER, FORMATTER)[:-1]
        else:
            return self.source

    @property
    def attachments(self):
        return self.cell.setdefault('attachments', {})

    def attach(self, path: Union[str, Path], attachment_name: Optional[str] = None):
        mime_type = get_mime_type(str(path))
        path = Path(path)
        attachment_name = attachment_name or path.name
        self.attachments[attachment_name] = {
            mime_type: base64.encodebytes(path.read_bytes()).decode('utf-8')
        }

    @property
    def html(self):
        renderer = IPythonRenderer(
            escape=False, attachments=self.attachments, exclude_anchor_links=True
        )
        return MarkdownWithMath(renderer=renderer).render(self.source)

    @property
    def soup(self):
        return BeautifulSoup(self.html, self._bs4_parser)


class RawCell(Cell, cell_type='raw'):
    pass
