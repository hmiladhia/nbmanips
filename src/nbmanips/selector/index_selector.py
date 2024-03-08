from functools import partial
from typing import Callable

from nbmanips.cell import Cell
from nbmanips.selector.base_selectors import SelectorBase


def _selector(cell: Cell, index: int) -> bool:
    return cell.num == index


class IndexSelector(SelectorBase):
    def __init__(self, index: int):
        self._index = index
        super().__init__()

    def get_callable(self, nb: dict) -> Callable[[Cell], bool]:
        index = self._index
        if index < 0:
            index = len(nb) + index
        return partial(_selector, index=index)
