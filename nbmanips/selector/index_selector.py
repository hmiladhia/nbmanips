from functools import partial
from typing import Callable

from ..cell import Cell
from . import SelectorBase


class IndexSelector(SelectorBase):
    def __init__(self, index: int):
        self._index = index
        super().__init__()

    def get_callable(self, nb: dict) -> Callable:
        index = self._index
        if index < 0:
            index = len(nb) + index
        return partial(self.selector, index=index)

    @classmethod
    def selector(cls, cell: Cell, index):
        return cell.num == index
