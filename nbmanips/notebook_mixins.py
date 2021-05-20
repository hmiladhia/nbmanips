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

    def __getitem__(self, item):
        return self.nb[item]

    def __setitem__(self, item, value):
        self.nb[item] = value

    def __len__(self):
        if self.nb is None or 'cells' not in self.nb:
            return 0
        return len(self.nb['cells'])

    def __repr__(self):
        if self.name:
            return f'<Notebook "{self.name}">'
        else:
            return f"<Notebook>"


class SlideShowMixin(NotebookBase):
    def mark_slideshow(self):
        self.nb['metadata']["celltoolbar"] = "Slideshow"

    def set_slide(self, selector, *args, **kwargs):
        self.tag_slide('slide', selector, *args, **kwargs)

    def set_skip(self, selector, *args, **kwargs):
        self.tag_slide('skip', selector, *args, **kwargs)

    def set_subslide(self, selector, *args, **kwargs):
        self.tag_slide('subslide', selector, *args, **kwargs)

    def set_fragment(self, selector, *args, **kwargs):
        self.tag_slide('fragment', selector, *args, **kwargs)

    def set_notes(self, selector, *args, **kwargs):
        self.tag_slide('notes', selector, *args, **kwargs)

    def tag_slide(self, tag, selector, *args, **kwargs):
        assert tag in {'-', 'skip', 'slide', 'subslide', 'fragment', 'notes'}
        self.tag('slideshow', {'slide_type': tag}, selector, *args, **kwargs)

    def tag(self, tag_key, tag, selector, *args, **kwargs):
        raise NotImplemented()
