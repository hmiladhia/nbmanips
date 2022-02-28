from abc import ABC, abstractmethod
from copy import copy
from itertools import filterfalse
from typing import Callable, Dict, List, Optional, Tuple, Union

from nbmanips.cell import Cell, MarkdownCell
from nbmanips.utils import partial


class ISelector(ABC):
    def __init__(self):
        self._neg = False

    @abstractmethod
    def get_callable(self, nb: dict) -> Callable[..., bool]:
        pass

    def iter_cells(self, nb, neg=False):
        selector = self.get_callable(nb)
        filter_method = filterfalse if (self._neg ^ neg) else filter
        return filter_method(
            selector, (Cell(cell, i) for i, cell in enumerate(nb['cells']))
        )

    def __invert__(self):
        selector = copy(self)
        selector._neg = not selector._neg
        return selector

    def __and__(self, other: 'ISelector'):
        if not isinstance(other, ISelector):
            return NotImplemented

        if isinstance(other, TrueSelector):
            return other & self

        return ListSelector([self]) & other

    def __or__(self, other: 'ISelector'):
        if not isinstance(other, ISelector):
            return NotImplemented

        if isinstance(other, TrueSelector):
            return other & self

        return ListSelector([self], type='or') | other


class Selector(ISelector):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def __new__(cls, selector, *args, **kwargs):
        if callable(selector):
            return CallableSelector(selector, *args, **kwargs)
        elif isinstance(selector, int):
            return IndexSelector(selector)
        elif isinstance(selector, str):
            return DefaultSelector(selector, *args, **kwargs)
        elif hasattr(selector, '__iter__'):
            return ListSelector(selector, *args, **kwargs)
        elif isinstance(selector, slice):
            assert not kwargs and not args
            return SliceSelector(selector)
        elif isinstance(selector, ISelector):
            return selector
        elif selector is None:
            return TrueSelector()
        raise ValueError(
            f'selector needs to be of type: (str, int, list, slice, NoneType): {type(selector)}'
        )

    def get_callable(self, nb: dict) -> Callable:
        raise NotImplementedError()


class TrueSelector(ISelector):
    def iter_cells(self, nb, neg=False):
        if self._neg ^ neg:
            return (_ for _ in range(0))
        return (Cell(cell, i) for i, cell in enumerate(nb['cells']))

    def get_callable(self, nb):
        return lambda cell: True

    def __and__(self, other: 'ISelector'):
        if not isinstance(other, ISelector):
            return NotImplemented

        if self._neg:
            return copy(self)
        return copy(other)

    def __or__(self, other: 'ISelector'):
        if not isinstance(other, ISelector):
            return NotImplemented

        if self._neg:
            return copy(other)
        return copy(self)


class CallableSelector(ISelector):
    def __init__(self, selector, *args, **kwargs):
        if args or kwargs:
            self._selector = partial(selector, *args, **kwargs)
        else:
            self._selector = selector
        super().__init__()

    def get_callable(self, nb: dict) -> Callable:
        return self._selector


class DefaultSelector(CallableSelector):
    default_selectors: Dict[str, Callable] = {}

    def __init__(self, selector: str, *args, **kwargs):
        # TODO: use signature ?
        callable_selector = self.default_selectors[selector]
        super(DefaultSelector, self).__init__(callable_selector, *args, **kwargs)

    @classmethod
    def register_selector(cls, key, selector):
        cls.default_selectors[key] = selector


class SliceSelector(ISelector):
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


class IndexSelector(ISelector):
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


class ListSelector(ISelector):
    def __init__(self, selector, *args, **kwargs):
        selector = list(selector)
        if len(args) == len(selector):
            args_kwargs_list = args
        else:
            args_kwargs_list = tuple(args[0]) if args else tuple({} for _ in selector)

        # Parsing args
        args_list, kwargs_list = self.__parse_list_args(args_kwargs_list)

        # Creating list of selectors
        self._and = self._check_sanity(kwargs)
        self._list: List[ISelector] = [
            Selector(sel, *args, **kwargs)
            for sel, args, kwargs in zip(selector, args_list, kwargs_list)
        ]
        super().__init__()

    def __and__(self, other: ISelector):
        if not isinstance(other, ISelector):
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

    def __or__(self, other: ISelector):
        if not isinstance(other, ISelector):
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


# Default Selectors


def contains(cell, text, case=True, output=False, regex=False):
    """
    Selects Cells containing a certain text.

    :param cell: Cell object to select
    :param text: a string to find in cell
    :param case: True if the search is case sensitive
    :type case: default True
    :param output: True if you want the search in the output of the cell too
    :type output: default False
    :param regex: boolean whether to use regex or not
    :return: a bool object (True if cell should be selected)
    """
    return cell.contains(text, case=case, output=output, regex=regex)


def has_type(cell, type):
    """
    Selects cells with the given type

    :param cell: Cell object to select
    :param type:
    :return: a bool object (True if cell should be selected)
    """
    return cell.type == type


def is_code(cell):
    """
    Selects code cells

    :param cell: Cell object to select
    :return: a bool object (True if cell should be selected)
    """
    return has_type(cell, 'code')


def is_markdown(cell):
    """
    Selects markdown cells

    :param cell: Cell object to select
    :return: a bool object (True if cell should be selected)
    """
    return has_type(cell, 'markdown')


def is_raw(cell):
    """
    Selects raw cells

    :param cell: Cell object to select
    :return: a bool object (True if cell should be selected)
    """
    return has_type(cell, 'raw')


def has_output(cell, value=True):
    """
    Checks if the cell has any output

    :param cell: Cell object to select
    :param value: set to False if you want to select cells with no output
    :return: a bool object (True if cell should be selected)
    """
    return (cell.output != '') == value


def has_output_type(cell, output_type: Union[set, str]):
    """
    Selects cells that have a given output_type

    :param cell: Cell object to select
    :param output_type: Output Type(MIME type) to select: text/plain, text/html, image/png, ...
    :type output_type: str
    :return: a bool object (True if cell should be selected)
    """
    if isinstance(output_type, str):
        output_types = {output_type}
    else:
        output_types = set(output_type)

    return cell.has_output_type(output_types)


def is_empty(cell):
    """
    Selects empty cells

    :param cell: Cell object to select
    :return: a bool object (True if cell should be selected)
    """
    return cell.source == '' and has_output(cell, False)


def has_byte_size(
    cell,
    min_size=0,
    max_size: Optional[int] = None,
    output_types=None,
    ignore_source=False,
):
    """
    Selects cells with byte size less than max_size and more than min_size.

    :param cell: Cell object to select
    :param min_size: int representing the minimum size
    :param max_size: int representing the maximum size
    :param output_types: Output Types(MIME type) to select: text/plain, text/html, image/png, ...
    :type output_types: set
    :param ignore_source: True if you want to get the size of the output only
    :return: a bool object (True if cell should be selected)
    """
    if isinstance(output_types, str):
        output_types = {output_types}

    size = cell.byte_size(output_types, ignore_source)

    return size >= min_size and (max_size is None or size < max_size)


def has_slide_type(cell, slide_type):
    """
    Selects markdown cells that have a given slide type

    :param cell: Cell object to select
    :param slide_type: Slide Type(s): '-', 'skip', 'slide', 'subslide', 'fragment', 'notes'
    :type slide_type: str / set / list
    :return: a bool object (True if cell should be selected)
    """
    if isinstance(slide_type, str):
        slide_type = {slide_type}

    return all(
        f(cell)
        for f in [
            lambda c: 'slideshow' in c.metadata,
            lambda c: 'slide_type' in c.metadata['slideshow'],
            lambda c: c.metadata['slideshow']['slide_type'] in slide_type,
        ]
    )


def has_tag(cell: Cell, tag: str, case=False):
    """
    Selects cells that have a certain tag

    :param cell: Cell object to select
    :param tag:
    :type tag: str
    :param case:
    :type case: bool
    :return: a bool object (True if cell should be selected)
    """
    if case:
        return tag in cell.metadata.get('tags', {})
    else:
        return tag.lower() in {
            cell_tag.lower() for cell_tag in cell.metadata.get('tags', {})
        }


def has_html_tag(cell: MarkdownCell, css_selector: str):
    """
    Select cells that have a certain HTML tag

    :param cell: Cell object to select
    :param css_selector: Css selector
    :type css_selector: str
    :return: a bool object (True if cell should be selected)
    """
    if not is_markdown(cell):
        return False

    return bool(cell.soup.select(css_selector))


def is_new_slide(cell, subslide=True):
    """
    Selects cells where a new slide/subslide starts
    :param cell: Cell object to select
    :param subslide: False if subslides should not be selected
    :return: a bool object (True if cell should be selected)
    """
    slide_types = {'slide'}
    if subslide:
        slide_types.add('subslide')
    return has_slide_type(cell, slide_types)


# Default Selectors
DefaultSelector.register_selector('contains', contains)
DefaultSelector.register_selector('empty', is_empty)
DefaultSelector.register_selector('is_empty', is_empty)
DefaultSelector.register_selector('has_output', has_output)
DefaultSelector.register_selector('has_output_type', has_output_type)
DefaultSelector.register_selector('has_byte_size', has_byte_size)
DefaultSelector.register_selector('has_html_tag', has_html_tag)
DefaultSelector.register_selector('has_tag', has_tag)

# Cell Types
DefaultSelector.register_selector('has_type', has_type)
DefaultSelector.register_selector('raw_cells', is_raw)
DefaultSelector.register_selector('is_raw', is_raw)
DefaultSelector.register_selector('markdown_cells', is_markdown)
DefaultSelector.register_selector('is_markdown', is_markdown)
DefaultSelector.register_selector('code_cells', is_code)
DefaultSelector.register_selector('is_code', is_code)

# Slide cells
DefaultSelector.register_selector('has_slide_type', has_slide_type)
DefaultSelector.register_selector('is_new_slide', is_new_slide)
