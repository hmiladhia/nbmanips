import copy

from nbmanips.cell import Cell
from nbmanips.selector import Selector


class NotebookBase:
    def __init__(self, content, name=None):
        self.raw_nb = copy.deepcopy(content)
        self.name = name
        self._selector = None

    def select(self, selector, *args, **kwargs) -> 'NotebookBase':
        notebook_selection = self.__class__(None, self.name)
        notebook_selection.raw_nb = self.raw_nb
        notebook_selection._selector = self.__get_new_selector(selector, *args, **kwargs)
        return notebook_selection

    def iter_cells(self, neg=False):
        return Selector(self._selector).iter_cells(self.raw_nb, neg=neg)

    @property
    def cells(self):
        return self.raw_nb['cells']

    @property
    def metadata(self):
        return self.raw_nb['metadata']

    def __add__(self, other: 'NotebookBase'):
        if not isinstance(other, NotebookBase):
            raise ValueError('Expected Notebook object, got %s' % type(other))

        # Copying the notebook
        raw_nb = copy.deepcopy(self.raw_nb)

        # Concatenating the notebooks
        raw_nb['cells'] = raw_nb['cells'] + copy.deepcopy(other.raw_nb['cells'])
        return self.__class__(raw_nb)

    def __mul__(self, other: int):
        if not isinstance(other, int):
            raise ValueError('Expected int, got %s' % type(other))

        # Copying the notebook
        raw_nb = copy.deepcopy(self.raw_nb)

        # Concatenating the notebooks
        raw_nb['cells'] = [].extend(copy.deepcopy(raw_nb['cells']) for _ in range(other))
        return self.__class__(raw_nb)

    def __getitem__(self, item):
        if isinstance(item, tuple):
            return self.select(*item)
        return self.select(item)

    def __len__(self):
        if self.raw_nb is None or 'cells' not in self.raw_nb:
            return 0
        return len(self.raw_nb['cells'])

    def __repr__(self):
        if self.name:
            return f'<Notebook "{self.name}">'
        else:
            return "<Notebook>"

    def __str__(self):
        return '\n'.join(str(Cell(cell, i, self.raw_nb)) for i, cell in enumerate(self.cells))

    def __get_new_selector(self, selector, *args, **kwargs):
        selector = selector if isinstance(selector, Selector) else Selector(selector, *args, **kwargs)
        if self._selector is None:
            new_selector = []
        else:
            new_selector = self._selector.copy()
        new_selector.append(selector)
        return new_selector
