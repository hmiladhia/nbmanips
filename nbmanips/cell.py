try:
    from html2text import html2text
except ImportError:
    html2txt = None

from nbmanips.utils import printable_cell


class Cell:
    def __init__(self, content, num=None):
        self.cell = content
        self.num = num

    def __getitem__(self, key):
        return self.cell[key]

    def __setitem__(self, key, value):
        self.cell[key] = value

    @property
    def type(self):
        return self.cell['cell_type']

    @property
    def metadata(self):
        return self.cell['metadata']

    @property
    def source(self):
        return self.get_source()

    @property
    def output(self):
        return self.get_output(text=True, readable=True).strip()

    def get_output(self, text=True, readable=True, preferred_data_types=None, exclude_data_types=None,
                   exclude_errors=True):
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

        preferred_data_types = ["text/plain", "text/html"] if preferred_data_types is None else preferred_data_types
        exclude_data_types = {'image/png'} if exclude_data_types is None else exclude_data_types
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
                            if readable and data_type == 'text/html':
                                if callable(html2text):
                                    output_text = html2text(output_text)
                                else:
                                    raise ModuleNotFoundError('You need to pip install html2txt for readable option')
                            processed_outputs.append(output_text)
                            break
                else:
                    for data_type, output_text in data.items():
                        if data_type in exclude_data_types:
                            continue
                        if text and not isinstance(output_text, str):
                            output_text = '\n'.join(output_text)
                        if readable and data_type == 'text/html':
                            if callable(html2text):
                                output_text = html2text(output_text)
                            else:
                                raise ModuleNotFoundError('You need to pip install html2txt for readable option')
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

    def __repr__(self):
        return f"<Cell {self.num}>" if self.num else "<Cell>"

    def __str__(self):
        if self.type == 'code':
            sources = [printable_cell(self.source)]
            if self.output:
                sources.append(self.output)
            return '\n'.join(sources)
        else:
            return self.source
