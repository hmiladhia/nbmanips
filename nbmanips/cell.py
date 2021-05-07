class Cell:
    def __init__(self, content, num=None):
        self.cell = content
        self.num = num

    @property
    def type(self):
        return self.cell['cell_type']

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

    def __getitem__(self, key):
        return self.cell[key]
