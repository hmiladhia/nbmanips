import shutil
from typing import Any, Optional, Union

from nbmanips.cell_utils import printable_cell
from nbmanips.cell_utils import get_readable


class Cell:
    def __init__(self, content, num=None, nb=None):
        self.cell = content
        self._num = num
        self.nb = nb

    def __getitem__(self, key):
        return self.cell[key]

    def __setitem__(self, key, value):
        self.cell[key] = value

    @property
    def type(self):
        return self.cell['cell_type']

    @property
    def num(self):
        return self._num

    @property
    def previous_cell(self):
        if self.num > 0 and self.nb is not None:
            return Cell(self.nb['cells'][self.num-1], self.num-1, self.nb)
        else:
            raise ValueError

    @property
    def next_cell(self):
        if self.nb is not None and self.num < (len(self.nb['cells'])-1):
            return Cell(self.nb['cells'][self.num + 1], self.num + 1, self.nb)
        else:
            raise ValueError

    @property
    def metadata(self):
        return self.cell['metadata']

    @property
    def source(self):
        return self.get_source().strip()

    @property
    def output(self):
        return self.get_output(text=True, readable=True).strip()

    def get_output(self, text=True, readable=True, preferred_data_types=None, exclude_data_types=None,
                   exclude_errors=True, **kwargs):
        """
        Tries its best to return a readable output from cell

        :param preferred_data_types:
        :param exclude_data_types:
        :param exclude_errors:
        :param text:
        :param readable:
        :return:
        """
        if self.type != "code":
            return ''

        # Default Values
        default_data_types = ['text/plain', 'text/html', 'image/png']
        if readable:
            default_data_types.reverse()

        preferred_data_types = default_data_types if preferred_data_types is None else preferred_data_types
        exclude_data_types = {} if exclude_data_types is None else exclude_data_types

        outputs = self.cell.get('outputs', [])
        processed_outputs = []
        for output in outputs:
            # output_type can be : (stream, execute_result, display_data, error)
            if output['output_type'] == 'stream':
                output_text = output['text']
                if text and not isinstance(output_text, str):
                    output_text = '\n'.join(output_text)
                processed_outputs.append(output_text)
            elif output['output_type'] in {'execute_result', 'display_data'}:
                data = output['data']
                if (set(preferred_data_types)-set(exclude_data_types)) & set(data.keys()):
                    for data_type in preferred_data_types:
                        if data_type not in exclude_data_types and data_type in data:
                            output_text = data[data_type]
                            if text and not isinstance(output_text, str):
                                output_text = '\n'.join(output_text)
                            if readable:
                                output_text = get_readable(output_text, data_type, **kwargs)

                            processed_outputs.append(output_text)
                            break
                else:
                    for data_type, output_text in data.items():
                        if data_type in exclude_data_types:
                            continue
                        if text and not isinstance(output_text, str):
                            output_text = '\n'.join(output_text)
                        if readable:
                            output_text = get_readable(output_text, data_type, **kwargs)
                        processed_outputs.append(output_text)
                        break
            elif output['output_type'] == 'error':
                if not exclude_errors:
                    raise NotImplemented("Errors aren't supported yet")
        if text:
            return '\n'.join(processed_outputs)
        return processed_outputs

    def get_source(self, text=True):
        source = self.cell['source']

        if isinstance(source, str):
            return source

        if text:
            return '\n'.join(source)
        return source

    def set_source(self, content, text=False):
        if text:
            content = content.split('\n')
        self.cell['source'] = content

    def contains(self, text, case=True, output=False):
        search_target = self.source
        if output:
            search_target += self.output

        if not case:
            text = text.lower()
            search_target = search_target.lower()
        return text in search_target

    def to_str(self, width=None, style='single', color=None, img_color=None, img_width=None):
        if self.type == 'code':
            width = width or (shutil.get_terminal_size().columns - 1)
            img_width = img_width if img_width else int(width*0.8)
            sources = [printable_cell(self.source, width=width, style=style, color=color)]

            img_color = bool(color) if img_color is None else img_color
            output = self.get_output(text=True, readable=True, colorful=img_color, width=img_width).strip()
            if output:
                sources.append(output)
            return '\n'.join(sources)
        else:
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
