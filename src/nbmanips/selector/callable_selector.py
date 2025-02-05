from functools import wraps
from typing import Callable

from nbmanips.cell import Cell
from nbmanips.selector.base_selectors import SelectorBase


class CallableSelector(SelectorBase):
    def __init__(self, selector: Callable[..., bool], *args, **kwargs):
        if args or kwargs:
            self._selector = _rpartial(selector, *args, **kwargs)
        else:
            self._selector = selector
        super().__init__()

    def get_callable(self, nb: dict) -> Callable[[Cell], bool]:
        return self._selector


def _rpartial(func, *args, **keywords):
    @wraps(func)
    def new_func(*f_args, **f_keywords):
        new_keywords = {**f_keywords, **keywords}
        return func(*f_args, *args, **new_keywords)

    return new_func
