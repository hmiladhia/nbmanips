import copy


class NotebookBase:
    def __init__(self, content, name=None):
        self.nb = copy.deepcopy(content)
        self.name = name

    def __add__(self, other):
        # Copying the notebook
        nb = copy.deepcopy(self.nb)

        # Concatenating the notebooks
        nb['cells'] = nb['cells'] + other.nb['cells']
        return self.__class__(nb)

    def __repr__(self):
        if self.name:
            return f"<Notebook {self.name}>"
        else:
            return f"<Notebook>"


class SlideShowMixin(NotebookBase):
    def slide(self, selector):
        self.tag_slide('slide', selector)

    def skip(self, selector):
        self.tag_slide('skip', selector)

    def tag_slide(self, tag, selector):
        # assert tag in {'skip', 'slide', }  TODO: complete list
        self.tag('slideshow', {'slide_type': tag}, selector)

    def tag(self, tag_key, tag, selctor):
        raise NotImplemented
