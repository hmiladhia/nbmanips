from typing import Optional

from nbmanips.cell_utils import get_readable
from nbmanips.utils import total_size


class CellOutput:
    output_type = None
    output_types = None

    def __init__(self, content):
        self.content = content
        assert self.content['output_type'] == self.output_type

    def to_str(self, *args, **kwargs):
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
        raise NotImplementedError()

    def byte_size(self, output_types: Optional[set]):
        if output_types is None or self.has_output_type(output_types):
            return total_size(self.content)
        return 0

    @classmethod
    def new(cls, content, build_output_types=False):
        if build_output_types or cls.output_types is None:
            cls.output_types = cls._get_output_types()

        output_class = cls.output_types[content['output_type']]
        return output_class(content)

    @classmethod
    def _get_output_types(cls):
        output_types = {}
        for output_class in cls.__subclasses__():
            if output_class.output_type is None:
                output_types.update(output_class._get_output_types())
            else:
                output_types[output_class.output_type] = output_class
        return output_types


class StreamOutput(CellOutput):
    output_type = 'stream'

    @property
    def text(self):
        return self.content['text']

    def to_str(self, *args, **kwargs):
        output_text = self.text
        if not isinstance(output_text, str):
            output_text = '\n'.join(output_text)
        return output_text

    def erase_output(self, output_types: set):
        return None if output_types & {'text/plain', 'text'} else self.content

    def has_output_type(self, output_types: set):
        return output_types & {'text/plain', 'text'}


class DataOutput(CellOutput):
    default_data_types = ['text/plain', 'text/html', 'image/png']

    def to_str(self, parse=False, exclude_data_types=None, *args, **kwargs):
        preferred_data_types = self.default_data_types if parse else reversed(self.default_data_types)
        exclude_data_types = {} if exclude_data_types is None else set(exclude_data_types)

        data = self.content['data']
        data_types = preferred_data_types + list(data.keys())
        for data_type in data_types:
            if data_type in exclude_data_types or data_type not in data:
                continue

            output_text = data[data_type]
            if not isinstance(output_text, str):
                output_text = '\n'.join(output_text)

            if parse:
                output_text = get_readable(output_text, data_type, **kwargs)
            return output_text

    def erase_output(self, output_types: set):
        for key in output_types:
            self.content['data'].pop(key, None)

        if not self.content['data']:
            return None

        return self.content

    def has_output_type(self, output_types: set):
        return output_types & set(self.content['data'])

    def byte_size(self, output_types: Optional[set]):
        if output_types is None:
            return total_size(self.content)
        elif not self.has_output_type(output_types):
            return 0
        else:
            return total_size({key: value for key, value in self.content['data'].items() if key in output_types})


class ErrorOutput(CellOutput):
    output_type = 'error'

    @property
    def ename(self):
        return self.content['ename']

    @property
    def evalue(self):
        return self.content['evalue']

    @property
    def traceback(self):
        return self.content['traceback']

    def to_str(self, *args, **kwargs):
        return '\n'.join(self.traceback + [f"{self.ename}: {self.evalue}"])

    def erase_output(self, output_types: set):
        return None if self.has_output_type(output_types) else self.content

    def has_output_type(self, output_types):
        return output_types & {'text/error', 'error'}


class DisplayData(DataOutput):
    output_type = 'display_data'


class ExecuteResult(DataOutput):
    output_type = 'execute_result'
