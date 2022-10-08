from abc import ABC, abstractmethod
from copy import copy
from itertools import filterfalse
from typing import Callable, Iterator, List, Tuple

from nbmanips._utils import partial
from nbmanips.cell import Cell


class SelectorBase(ABC):
    def __init__(self):
        self._neg = False

    @abstractmethod
    def get_callable(self, nb: dict) -> Callable[..., bool]:
        pass

    def iter_cells(self, nb, neg=False) -> Iterator[Cell]:
        selector = self.get_callable(nb)
        filter_method = filterfalse if (self._neg ^ neg) else filter
        return filter_method(
            selector, (Cell(cell, i) for i, cell in enumerate(nb['cells']))
        )

    def __invert__(self):
        selector = copy(self)
        selector._neg = not selector._neg
        return selector

    def __and__(self, other: 'SelectorBase'):
        if not isinstance(other, SelectorBase):
            return NotImplemented

        if isinstance(other, TrueSelector):
            return other & self

        return ListSelector([self]) & other

    def __or__(self, other: 'SelectorBase'):
        if not isinstance(other, SelectorBase):
            return NotImplemented

        if isinstance(other, TrueSelector):
            return other & self

        return ListSelector([self], type='or') | other


class TrueSelector(SelectorBase):
    def iter_cells(self, nb, neg=False) -> Iterator[Cell]:
        if self._neg ^ neg:
            return (_ for _ in range(0))
        return (Cell(cell, i) for i, cell in enumerate(nb['cells']))

    def get_callable(self, nb):
        return lambda cell: True

    def __and__(self, other: 'SelectorBase'):
        if not isinstance(other, SelectorBase):
            return NotImplemented

        if self._neg:
            return copy(self)
        return copy(other)

    def __or__(self, other: 'SelectorBase'):
        if not isinstance(other, SelectorBase):
            return NotImplemented

        if self._neg:
            return copy(other)
        return copy(self)


class ListSelector(SelectorBase):
    def __init__(self, selector, *args, **kwargs):
        from . import Selector

        selector = list(selector)
        if len(args) == len(selector):
            args_kwargs_list = args
        else:
            args_kwargs_list = tuple(args[0]) if args else tuple({} for _ in selector)

        # Parsing args
        args_list, kwargs_list = self.__parse_list_args(args_kwargs_list)

        # Creating list of selectors
        self._and = self._check_sanity(kwargs)
        self._list: List[SelectorBase] = [
            Selector(sel, *args, **kwargs)
            for sel, args, kwargs in zip(selector, args_list, kwargs_list)
        ]
        super().__init__()

    def __and__(self, other: SelectorBase):
        if not isinstance(other, SelectorBase):
            return NotImplemented

        if not self._and:
            return super().__and__(other)

        selector = copy(self)
        selector._list = copy(selector._list)
        if isinstance(other, ListSelector) and (other._and == self._and):
            selector._list.extend(other._list)
        else:
            selector._list.append(other)
        return selector

    def __or__(self, other: SelectorBase):
        if not isinstance(other, SelectorBase):
            return NotImplemented

        if self._and:
            return super().__or__(other)

        selector = copy(self)
        selector._list = copy(selector._list)
        if isinstance(other, ListSelector) and (other._and == self._and):
            selector._list.extend(other._list)
        else:
            selector._list.append(other)
        return selector

    def get_callable(self, nb: dict) -> Callable:
        op = all if self._and else any
        return partial(self.__combine, op=op, nb=nb)

    def __combine(self, cell: Cell, op, nb):
        return op((sel._neg ^ sel.get_callable(nb)(cell)) for sel in self._list)

    @staticmethod
    def _check_sanity(kwargs):
        _type = kwargs.pop('type', 'and')
        if _type not in {'and', 'or'}:
            raise ValueError('type can only have the following values: {"and", "or"}')

        if kwargs:
            raise ValueError("only 'type' keyword is allowed as keyword argument")

        return _type == 'and'

    @staticmethod
    def __parse_list_args(list_args: tuple) -> Tuple[list, list]:
        args_list: list = []
        kwargs_list: list = []
        for arg in list_args:
            if isinstance(arg, dict):
                args_list.append([])
                kwargs_list.append(arg)
            elif (
                isinstance(arg, tuple)
                and len(arg) == 2
                and hasattr(arg[0], '__iter__')
                and isinstance(arg[1], dict)
            ):
                args_list.append(arg[0])
                kwargs_list.append(arg[1])
            elif hasattr(arg, '__iter__'):
                args_list.append(arg)
                kwargs_list.append({})
            else:
                raise ValueError('Cannot parse arguments:', str(arg))
        return args_list, kwargs_list
