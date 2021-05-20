try:
    from html2txt import html2txt
except ImportError:
    html2txt = None


class Cell:
    def __init__(self, content, num=None):
        self.cell = content
        self.num = num

    @property
    def type(self):
        return self.cell['cell_type']

    @property
    def metadata(self):
        return self.cell['metadata']

    @property
    def output(self):
        return self.get_output(text=True, readable=True)

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
        assert self.type == "code", 'Only code cells have outputs'
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
                if set(preferred_data_types) & set(data.keys()):
                    for data_type in preferred_data_types:
                        if data_type not in exclude_data_types and data_type in data:
                            output_text = data[data_type]
                            if text and not isinstance(output_text, str):
                                output_text = '\n'.join(output_text)
                            if readable and data_type == 'text/html':
                                if callable(html2txt):
                                    output_text = html2txt(output_text)
                                else:
                                    raise ModuleNotFoundError('You need to pip install html2txt for readable option')
                            processed_outputs.append(output_text)
                            break
                else:
                    for data_type, output_text in data.items():
                        if text and not isinstance(output_text, str):
                            output_text = '\n'.join(output_text)
                        if readable and data_type == 'text/html':
                            if callable(html2txt):
                                output_text = html2txt(output_text)
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

    @property
    def source(self):
        return self.get_source()

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
        if output:
            raise NotImplemented()

        if not case:
            text = text.lower()
            source = self.get_source().lower()
        else:
            source = self.get_source()
        return text in source
