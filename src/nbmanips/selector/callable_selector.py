from typing import Callable

from nbmanips._utils import partial
from nbmanips.cell import Cell
from nbmanips.selector.base_selectors import SelectorBase


class CallableSelector(SelectorBase):
    def __init__(self, selector: Callable[..., bool], *args, **kwargs):
        if args or kwargs:
            self._selector = partial(selector, *args, **kwargs)
        else:
            self._selector = selector
        super().__init__()

    def get_callable(self, nb: dict) -> Callable[[Cell], bool]:
        return self._selector
