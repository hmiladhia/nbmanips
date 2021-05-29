import copy
from nbmanips import Cell
from nbmanips import Selector
from nbmanips.selector import is_new_slide, has_slide_type


class NotebookBase:
    def __init__(self, content, name=None):
        self._nb = copy.deepcopy(content)
        self.name = name

    def __add__(self, other: 'NotebookBase'):
        # Copying the notebook
        nb = copy.deepcopy(self._nb)

        # Concatenating the notebooks
        nb['cells'] = nb['cells'] + other._nb['cells']
        return self.__class__(nb)

    def __getitem__(self, item):
        return self._nb[item]

    def __setitem__(self, item, value):
        self._nb[item] = value

    def __len__(self):
        if self._nb is None or 'cells' not in self._nb:
            return 0
        return len(self._nb['cells'])

    def __repr__(self):
        if self.name:
            return f'<Notebook "{self.name}">'
        else:
            return f"<Notebook>"

    def __str__(self):
        return '\n'.join(str(Cell(cell, i, self._nb)) for i, cell in enumerate(self.cells))

    def iter_cells(self, selector=None, *args, **kwargs):
        return Selector(selector, *args, **kwargs).iter_cells(self._nb)

    def iter_neg_cells(self, selector, *args, **kwargs):
        return Selector(selector, *args, **kwargs).iter_cells(self._nb, neg=True)

    @property
    def cells(self):
        return self._nb['cells']


class SlideShowMixin(NotebookBase):
    def mark_slideshow(self):
        self._nb['metadata']["celltoolbar"] = "Slideshow"

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

    def max_cells_per_slide(self, n_cells=3):
        slides_count = 0
        for cell in self.iter_cells():
            if is_new_slide(cell):
                slides_count = 0
            elif has_slide_type(cell, {'skip', 'fragment', 'notes'}):
                # Don't count
                pass
            else:
                slides_count += 1

            if slides_count > n_cells:
                if 'slideshow' in cell.cell['metadata']:
                    cell.metadata['slideshow']['slide_type'] = 'subslide'
                else:
                    cell.metadata['slideshow'] = {'slide_type': 'subslide'}
                slides_count = 0

    def auto_slide(self, max_cells_per_slide=3):
        # Each title represents
        self.set_slide(['is_markdown', 'contains'], [], '#')

        # Create a new slide only
        for cell in reversed(list(self.iter_cells())):
            if cell.num > 0 and is_new_slide(cell.previous_cell):
                if 'slideshow' in cell.cell['metadata']:
                    cell.metadata['slideshow']['slide_type'] = '-'
                else:
                    cell.metadata['slideshow'] = {'slide_type': '-'}

        # Set max cells per slide
        self.max_cells_per_slide(max_cells_per_slide)
