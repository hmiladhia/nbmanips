import copy
from typing import Callable, Optional, Any

import nbformat

from nbmanips.cell import Cell
from nbmanips.selector import Selector


class NotebookBase:
    def __init__(self, content: dict, name=None, validate=True):
        if validate:
            self.__validate(content)
        self.raw_nb = copy.deepcopy(content)
        self.name = name
        self._selector = None

    def select(self, selector, *args, **kwargs):
        notebook_selection = self.reset_selection()
        notebook_selection._selector = self.__get_new_selector(selector, *args, **kwargs)
        return notebook_selection

    def apply(self, func: Callable[[Cell], Optional[Cell]], neg=False):
        delete_list = []
        for cell in self.iter_cells(neg):
            num = cell.num
            new_cell = func(cell)
            if new_cell is None:
                delete_list.append(num)
            else:
                self.cells[num] = new_cell.cell

        for num in reversed(delete_list):
            del self.cells[num]

    def map(self, func: Callable[[Cell], Any], neg=False):
        return list(map(func, self.iter_cells(neg)))

    def reset_selection(self):
        notebook_selection = self.__class__(None, self.name, validate=False)
        notebook_selection.raw_nb = self.raw_nb
        return notebook_selection

    def iter_cells(self, neg=False):
        return Selector(self._selector).iter_cells(self.raw_nb, neg=neg)

    @property
    def cells(self):
        return self.raw_nb['cells']

    @property
    def metadata(self):
        return self.raw_nb['metadata']

    @property
    def used_ids(self):
        return {cell['id'] for cell in self.cells if 'id' in cell}

    def first_cell(self):
        """
        Return the first selected cell
        :return:
        """
        for cell in self.iter_cells():
            return cell

    def last_cell(self):
        """
        Return the last selected cell
        :return:
        """
        for cell in reversed(list(self.iter_cells())):
            return cell

    def list_cells(self):
        """
        Return a list of the selected cells
        :return:
        """
        return [cell for cell in self.iter_cells()]

    def add_cell(self, cell, pos=None):
        pos = len(self) if pos is None else pos

        new_id = cell.id
        while new_id in self.used_ids:
            new_id = cell.generate_id_candidate()

        cell = cell.get_copy(new_id)
        self.cells.insert(pos, cell.cell)

    def __add__(self, other: 'NotebookBase'):
        if not isinstance(other, NotebookBase):
            raise ValueError('Expected Notebook object, got %s' % type(other))

        # Copying the notebook
        raw_nb = copy.deepcopy(self.raw_nb)

        # Creating empty Notebook
        raw_nb['cells'] = []
        new_nb = self.__class__(raw_nb)

        # Concatenating the notebooks
        for cell in (self.list_cells() + other.list_cells()):
            new_nb.add_cell(cell)

        return new_nb

    def __mul__(self, other: int):
        if not isinstance(other, int):
            raise ValueError('Expected int, got %s' % type(other))

        # Copying the notebook
        raw_nb = copy.deepcopy(self.raw_nb)

        # Creating empty Notebook
        raw_nb['cells'] = []
        new_nb = self.__class__(raw_nb)

        # Concatenating the notebooks
        for _ in range(other):
            for cell in self.iter_cells():
                new_nb.add_cell(cell)
        return new_nb

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
        return '\n'.join(str(cell) for cell in self.iter_cells())

    def create_selector(self, selector, *args, **kwargs):
        if isinstance(selector, int) and selector < 0:
            selector = len(self) + selector
        if isinstance(selector, slice):
            start, stop, step = selector.start, selector.stop, selector.step
            if stop is not None and stop < 0:
                stop = stop + len(self)
            if start is not None and start < 0:
                start = start + len(self)

            selector = slice(start, stop, step)

        if not isinstance(selector, Selector):
            selector = Selector(selector, *args, **kwargs)
        return selector

    def __get_new_selector(self, selector, *args, **kwargs):
        selector = self.create_selector(selector, *args, **kwargs)

        if self._selector is None:
            new_selector = []
        else:
            new_selector = self._selector.copy()
        new_selector.append(selector)
        return new_selector

    @staticmethod
    def __validate(content: dict):
        if not isinstance(content, dict):
            message = f"'content' must be of type 'dict': {type(content).__name__!r} given"
            if isinstance(content, str):
                message += "\nUse Notebook.read_ipynb(path) to read notebook from file"
            raise ValueError(message)
        nbformat.validate(nbdict=content)
