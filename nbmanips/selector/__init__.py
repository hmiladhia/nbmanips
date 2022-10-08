from typing import Callable

from .base_selectors import ListSelector, SelectorBase, TrueSelector


class Selector(SelectorBase):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def __new__(cls, selector, *args, **kwargs):
        if callable(selector):
            from .callable_selector import CallableSelector

            return CallableSelector(selector, *args, **kwargs)
        elif isinstance(selector, int):
            from .index_selector import IndexSelector

            return IndexSelector(selector)
        elif isinstance(selector, str):
            from .default_selector import DefaultSelector

            return DefaultSelector(selector, *args, **kwargs)
        elif hasattr(selector, '__iter__'):
            return ListSelector(selector, *args, **kwargs)
        elif isinstance(selector, slice):
            assert not kwargs and not args

            from .slice_selector import SliceSelector

            return SliceSelector(selector)
        elif isinstance(selector, SelectorBase):
            return selector
        elif selector is None:
            return TrueSelector()
        raise ValueError(
            f'selector needs to be of type: (str, int, list, slice, NoneType): {type(selector)}'
        )

    def get_callable(self, nb: dict) -> Callable:
        raise NotImplementedError()


__all__ = ['SelectorBase', 'Selector']
