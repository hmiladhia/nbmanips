import html
from typing import Optional, Union

from nbmanips.cell_utils import ParserBase
from nbmanips.cell_utils import TextParser
from nbmanips.cell_utils import HtmlParser
from nbmanips.cell_utils import ImageParser
from nbmanips.utils import total_size


def _get_output_types(output_type: Union[set, dict, str]) -> set:
    if isinstance(output_type, str):
        if '/' in output_type:
            return {output_type, output_type.split('/')[0]}
        return {output_type}

    output_types = set()
    for output in output_type:
        output_types |= _get_output_types(output)
    return output_types


def _to_html(text):
    return html.escape(text).encode('ascii', 'xmlcharrefreplace').decode('ascii')


class CellOutput:
    output_type = None
    _output_types = {}
    _parsers = {}

    def __init__(self, content):
        self.content = content

    @property
    def output_types(self) -> set:
        raise NotImplementedError()

    def to_str(self, parsers=None, parsers_config=None, excluded_data_types=None):
        return ''

    def to_html(self, excluded_data_types=None):
        return ''

    def erase_output(self, output_types: set):
        raise NotImplementedError()

    def has_output_type(self, output_types: set):
        """
        Select cells that have a given output_type

        :param output_types: Output Types(MIME types) to select: text/plain, text/html, image/png, ...
        :type output_types: set
        :return: a bool object (True if cell should be selected)
        """
        return output_types & self.output_types

    def byte_size(self, output_types: Optional[set]):
        if output_types is None or self.has_output_type(output_types):
            return total_size(self.content)
        return 0

    @classmethod
    def register_parser(cls, output_type, parser: ParserBase):
        cls._parsers[output_type] = parser

    @classmethod
    def get_parser(cls, parser_key: str, parser_config_dict: dict):
        if parser_key in cls._parsers:
            return cls._parsers[parser_key], parser_config_dict.get(parser_key, {})
        else:
            parser_key = parser_key.split('/')[0]
            return cls._parsers.get(parser_key, None), parser_config_dict.get(parser_key, {})

    @property
    def default_parsers(self) -> set:
        return {key for key, value in self._parsers.items() if value.default_state}

    def __new__(cls, content, *args, **kwargs):
        output_type = content['output_type']
        output_class = cls._output_types[output_type]
        obj = super().__new__(output_class)
        output_class.__init__(obj, content, *args, **kwargs)
        return obj

    def __init_subclass__(cls, output_type=None, **kwargs):
        super().__init_subclass__(**kwargs)
        if output_type:
            cls._output_types[output_type] = cls
        cls.output_type = output_type


class StreamOutput(CellOutput, output_type='stream'):
    @property
    def text(self):
        return self.content['text']

    @property
    def output_types(self):
        return _get_output_types('text/plain')

    def to_str(self, parsers=None, parsers_config=None, excluded_data_types=None):
        parsers_config = parsers_config or {}
        excluded_data_types = set() if excluded_data_types is None else set(excluded_data_types)
        if self.output_types & excluded_data_types:
            return ''

        output_text = self.text
        if not isinstance(output_text, str):
            output_text = '\n'.join(output_text)

        parser, parser_config = self.get_parser('text/plain', parsers_config)
        if parser:
            return parser.parse(output_text, **parser_config)
        return output_text

    def to_html(self, excluded_data_types=None):
        excluded_data_types = set() if excluded_data_types is None else set(excluded_data_types)
        if self.output_types & excluded_data_types:
            return ''
        output_text = self.text
        if not isinstance(output_text, str):
            output_text = '\n'.join(output_text)
        return _to_html(output_text)

    def erase_output(self, output_types: set):
        return None if self.has_output_type(output_types) else self.content


class DataOutput(CellOutput):
    _default_data_types = ['text', 'image', 'text/html']

    @classmethod
    def _get_key(cls, dt, parsers):
        alt_dt = dt.split('/')[0]
        s1 = dt not in parsers and alt_dt not in parsers
        s2 = -(cls._default_data_types.index(dt) if dt in cls._default_data_types else (
            cls._default_data_types.index(alt_dt) if alt_dt in cls._default_data_types else -1))
        return s1, s2

    def to_str(self, parsers=None, parsers_config=None, excluded_data_types=None):
        parsers = self.default_parsers if parsers is None else set(parsers)
        parsers_config = parsers_config or {}
        excluded_data_types = set() if excluded_data_types is None else set(excluded_data_types)

        data = self.content['data']
        for data_type in sorted(data, key=lambda x: self._get_key(x, parsers)):
            alt_data_types = _get_output_types(data_type)
            if alt_data_types & excluded_data_types:
                continue

            output_text = data[data_type]
            if not isinstance(output_text, str):
                output_text = '\n'.join(output_text)

            if alt_data_types & parsers:
                parser, parser_config = self.get_parser(data_type, parsers_config)
                if parser:
                    output_text = parser.parse(output_text, **parser_config)
            return output_text
        return ''

    def to_html(self, excluded_data_types=None):
        excluded_data_types = set() if excluded_data_types is None else set(excluded_data_types)

        data = self.content['data'].copy()
        for data_type in list(data.keys()):
            if _get_output_types(data_type) & excluded_data_types:
                data.pop(data_type, None)

        if 'text/html' in data:
            output_text = data['text/html']
            if not isinstance(output_text, str):
                output_text = '\n'.join(output_text)
            return output_text

        for data_type in data:
            if data_type.startswith('image'):
                content = data['image/png']
                return f'<img src="data:image/png;base64, {content}"/>'

        if 'text/plain' in data:
            output_text = data['text/plain']
            if not isinstance(output_text, str):
                output_text = '\n'.join(output_text)
            return _to_html(output_text)

        return ''

    def erase_output(self, output_types: set):
        for key in output_types:
            self.content['data'].pop(key, None)

        if not self.content['data']:
            return None

        return self.content

    @property
    def output_types(self):
        return _get_output_types(self.content['data'])

    def has_output_type(self, output_types: set):
        return output_types & self.output_types

    def byte_size(self, output_types: Optional[set]):
        if output_types is None:
            return total_size(self.content)
        elif not self.has_output_type(output_types):
            return 0
        else:
            return total_size({key: value for key, value in self.content['data'].items() if key in output_types})


class ErrorOutput(CellOutput, output_type='error'):
    @property
    def ename(self):
        return self.content['ename']

    @property
    def evalue(self):
        return self.content['evalue']

    @property
    def traceback(self):
        return self.content['traceback']

    @property
    def output_types(self):
        return _get_output_types('text/error')

    def to_str(self, parsers=None, parsers_config=None, excluded_data_types=None):
        parsers_config = parsers_config or {}
        excluded_data_types = set() if excluded_data_types is None else set(excluded_data_types)
        if self.output_types & excluded_data_types:
            return ''

        output_text = '\n'.join(self.traceback + [f"{self.ename}: {self.evalue}"])
        parser, parser_config = self.get_parser('text/error', parsers_config)
        if parser:
            return parser.parse(output_text, **parser_config)
        return output_text

    def to_html(self, excluded_data_types=None):
        excluded_data_types = set() if excluded_data_types is None else set(excluded_data_types)
        if self.output_types & excluded_data_types:
            return ''

        return _to_html('\n'.join(self.traceback + [f"{self.ename}: {self.evalue}"]))

    def erase_output(self, output_types: set):
        return None if self.has_output_type(output_types) else self.content


class DisplayData(DataOutput, output_type='display_data'):
    pass


class ExecuteResult(DataOutput, output_type='execute_result'):
    @property
    def execution_count(self):
        return self.content.get("execution_count", None)


CellOutput.register_parser('text', TextParser())
CellOutput.register_parser('text/html', HtmlParser())
CellOutput.register_parser('image', ImageParser())
