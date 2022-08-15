from typing import Callable

from nbmanips._utils import partial
from nbmanips.selector import SelectorBase


class CallableSelector(SelectorBase):
    def __init__(self, selector, *args, **kwargs):
        if args or kwargs:
            self._selector = partial(selector, *args, **kwargs)
        else:
            self._selector = selector
        super().__init__()

    def get_callable(self, nb: dict) -> Callable[..., bool]:
        return self._selector
