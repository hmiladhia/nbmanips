from abc import abstractmethod, ABC
from copy import copy
from itertools import filterfalse
from typing import Optional, Union, Callable, Tuple

from nbmanips.cell import Cell
from nbmanips.utils import partial


class ISelector(ABC):
    def __init__(self):
        self._neg = False

    @abstractmethod
    def get_callable(self, nb) -> Tuple[Callable, bool]:
        pass

    def iter_cells(self, nb, neg=False):
        selector, sel_neg = self.get_callable(nb)
        filter_method = filterfalse if (sel_neg ^ neg) else filter
        return filter_method(selector, (Cell(cell, i) for i, cell in enumerate(nb["cells"])))

    def __invert__(self):
        selector = copy(self)
        selector._neg = not selector._neg
        return selector

    def __and__(self, selector):
        return ListSelector([self, selector], type='and')

    def __or__(self, selector):
        return ListSelector([self, selector], type='or')


def Selector(selector, *args, **kwargs):
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
        return CallableSelector(lambda cell: True)   # TODO
    else:
        raise ValueError(f'selector needs to be of type: (str, int, list, slice, None): {type(selector)}')


class CallableSelector(ISelector):
    def __init__(self, selector, *args, **kwargs):
        if args or kwargs:
            self._selector = partial(selector, *args, **kwargs)
        else:
            self._selector = selector
        super().__init__()

    def get_callable(self, nb) -> Tuple[Callable, bool]:
        return self._selector, self._neg


class DefaultSelector(CallableSelector):
    # TODO: use signature
    default_selectors = {}

    def __init__(self, selector: str, *args, **kwargs):
        super(DefaultSelector, self).__init__(self.default_selectors[selector], *args, **kwargs)

    @classmethod
    def register_selector(cls, key, selector):
        cls.default_selectors[key] = selector


class SliceSelector(ISelector):
    def __init__(self, selector):
        self._slice = selector
        super().__init__()

    def get_callable(self, nb):
        new_slice = self.__adapt_slice(self._slice, len(nb))
        return self.__get_slice_selector(new_slice), self._neg

    @staticmethod
    def __adapt_slice(old_slice, n_cells):
        # TODO: Implement this
        return old_slice

    @classmethod
    def __get_slice_selector(cls, selector: slice) -> callable:
        start, stop, step = selector.start, selector.stop, selector.step
        if step and step < 0:
            start, stop = stop+1, start+1

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

    def get_callable(self, nb) -> Tuple[Callable, bool]:
        return partial(self.selector, index=self._index), self._neg

    @classmethod
    def selector(cls, cell: Cell, index):
        return cell.num == index


class ListSelector(ISelector):
    def __init__(self, selector, *args, **kwargs):
        selector = list(selector)
        self.type_ = kwargs.pop('type', 'and')
        assert not kwargs, "only 'type' keyword is allowed as keyword argument"
        if len(args) == len(selector):
            args_kwargs_list = args
        else:
            args_kwargs_list = tuple(args[0]) if args else tuple([{} for _ in selector])

        # Parsing args
        args_list, kwargs_list = self.__parse_list_args(args_kwargs_list)

        # Creating list of selectors
        self._selector_list = [
            Selector(sel, *args, **kwargs)
            for sel, args, kwargs in zip(selector, args_list, kwargs_list)
        ]
        super().__init__()

    def get_callable(self, nb) -> Tuple[Callable, bool]:
        if self.type_ == 'and':
            return lambda cell: all((sel._neg ^ sel.get_callable(nb)[0](cell)) for sel in self._selector_list), self._neg
        elif self.type_ == 'or':
            return lambda cell: any((sel._neg ^ sel.get_callable(nb)[0](cell)) for sel in self._selector_list), self._neg
        else:
            raise ValueError(f'type can be "and" or "or": {self.type_}')

    @staticmethod
    def __parse_list_args(list_args: tuple) -> (list, list):
        args_list, kwargs_list = [], []
        for arg in list_args:
            if isinstance(arg, dict):
                args_list.append([])
                kwargs_list.append(arg)
            elif isinstance(arg, tuple) and len(arg) == 2 and hasattr(arg[0], '__iter__') and isinstance(arg[1], dict):
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
    return (cell.output != "") == value


def has_output_type(cell, output_type: Union[set, str]):
    """
    Select cells that have a given output_type

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


def has_byte_size(cell, min_size=0, max_size: Optional[int] = None, output_types=None, ignore_source=False):
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
    Select cells that have a given slide type

    :param cell: Cell object to select
    :param slide_type: Slide Type(s): '-', 'skip', 'slide', 'subslide', 'fragment', 'notes'
    :type slide_type: str / set / list
    :return: a bool object (True if cell should be selected)
    """
    if isinstance(slide_type, str):
        slide_type = {slide_type}

    return all(f(cell) for f in [lambda c: 'slideshow' in c.metadata,
               lambda c: 'slide_type' in c.metadata['slideshow'],
               lambda c: c.metadata['slideshow']['slide_type'] in slide_type])


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
