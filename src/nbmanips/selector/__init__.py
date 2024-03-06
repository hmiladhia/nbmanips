from typing import Callable

from nbmanips.selector.base_selectors import ListSelector, SelectorBase, TrueSelector


class Selector(SelectorBase):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def __new__(cls, selector, *args, **kwargs):
        if callable(selector):
            from .callable_selector import CallableSelector

            selector = CallableSelector(selector, *args, **kwargs)
        elif isinstance(selector, int):
            from .index_selector import IndexSelector

            selector = IndexSelector(selector)
        elif isinstance(selector, str):
            from .default_selector import DefaultSelector

            selector = DefaultSelector(selector, *args, **kwargs)
        elif hasattr(selector, "__iter__"):
            selector = ListSelector(selector, *args, **kwargs)
        elif isinstance(selector, slice):
            if kwargs or args:
                raise ValueError

            from .slice_selector import SliceSelector

            selector = SliceSelector(selector)
        elif isinstance(selector, SelectorBase):
            pass
        elif selector is None:
            selector = TrueSelector()
        else:
            raise ValueError(
                f"selector needs to be of type: (str, int, list, slice, NoneType): {type(selector)}"
            )

        return selector

    def get_callable(self, nb: dict) -> Callable:
        raise NotImplementedError()


__all__ = ["SelectorBase", "Selector"]
