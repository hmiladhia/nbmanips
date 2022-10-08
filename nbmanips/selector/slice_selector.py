from functools import partial
from typing import Callable

from ..cell import Cell
from . import SelectorBase


class SliceSelector(SelectorBase):
    def __init__(self, selector):
        self._slice = selector
        super().__init__()

    def get_callable(self, nb: dict) -> Callable[[Cell], bool]:
        new_slice = self.__adapt_slice(self._slice, len(nb.get('cells', [])))
        return self.__get_slice_selector(new_slice)

    @staticmethod
    def __adapt_slice(old_slice, n_cells):
        start, stop, step = old_slice.start, old_slice.stop, old_slice.step
        if stop is not None and stop < 0:
            stop = stop + n_cells
        if start is not None and start < 0:
            start = start + n_cells

        new_slice = slice(start, stop, step)
        return new_slice

    @classmethod
    def __get_slice_selector(cls, selector: slice) -> Callable[[Cell], bool]:
        start, stop, step = selector.start, selector.stop, selector.step
        if step and step < 0:
            start, stop = stop + 1, start + 1

        selector_list = []
        if start is not None:
            selector_list.append(lambda cell: cell.num >= start)
        if stop is not None:
            selector_list.append(lambda cell: cell.num < stop)
        if step is not None:
            selector_list.append(lambda cell: (cell.num - start) % abs(step) == 0)
        return partial(cls.__get_multiple_selector, selector_list=selector_list)

    @staticmethod
    def __get_multiple_selector(cell, selector_list: list):
        return all(sel(cell) for sel in selector_list)
