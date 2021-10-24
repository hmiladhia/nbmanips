from itertools import filterfalse
from typing import Optional, Union

from nbmanips.cell import Cell
from nbmanips.utils import partial


class Selector:
    default_selectors = {}

    def __init__(self, selector, *args, **kwargs):
        self._selector = self._get_selector(selector, *args, **kwargs)

    def iter_cells(self, nb, neg=False):
        filter_method = filterfalse if neg else filter
        return filter_method(self._selector, (Cell(cell, i) for i, cell in enumerate(nb["cells"])))

    @classmethod
    def register_selector(cls, key, selector):
        cls.default_selectors[key] = selector

    def __and__(self, selector):
        return Selector([self, selector], type='and')

    def __or__(self, selector):
        return Selector([self, selector], type='or')

    def __invert__(self):
        return Selector(lambda cell: not self._selector(cell))

    def _get_selector(self, selector, *args, **kwargs):
        if callable(selector):
            return partial(selector, *args, **kwargs)
        elif isinstance(selector, int):
            return lambda cell: cell.num == selector
        elif isinstance(selector, str):
            return partial(self.default_selectors[selector], *args, **kwargs)
        elif hasattr(selector, '__iter__'):
            return self.__get_list_selector(selector, *args, **kwargs)
        elif isinstance(selector, slice):
            assert not kwargs and not args
            return self.__get_slice_selector(selector)
        elif isinstance(selector, Selector):
            return selector._selector
        elif selector is None:
            return lambda cell: True
        else:
            raise ValueError(f'selector needs to be of type: (str, int, list, slice, None): {type(selector)}')

    @classmethod
    def __get_list_selector(cls, selector, *args, **kwargs):
        selector = list(selector)
        type_ = kwargs.pop('type', 'and')
        assert not kwargs, "only 'type' keyword is allowed as keyword argument"
        if len(args) == len(selector):
            args_kwargs_list = args
        else:
            args_kwargs_list = tuple(args[0]) if args else tuple([{} for _ in selector])

        # Parsing args
        args_list, kwargs_list = cls.__parse_list_args(args_kwargs_list)

        # Creating list of selectors
        selector_list = [Selector(sel, *args, **kwargs) for sel, args, kwargs in zip(selector, args_list, kwargs_list)]

        # Return selector function
        if type_ == 'and':
            return lambda cell: all(sel._selector(cell) for sel in selector_list)
        elif type_ == 'or':
            return lambda cell: any(sel._selector(cell) for sel in selector_list)
        else:
            raise ValueError(f'type can be "and" or "or": {type_}')

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
        return cls.__get_multiple_selector(selector_list)

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

    @staticmethod
    def __get_multiple_selector(selector_list: list):
        return lambda cell: all(sel(cell) for sel in selector_list)


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
Selector.register_selector('contains', contains)
Selector.register_selector('empty', is_empty)
Selector.register_selector('is_empty', is_empty)
Selector.register_selector('has_output', has_output)
Selector.register_selector('has_output_type', has_output_type)
Selector.register_selector('has_byte_size', has_byte_size)

# Cell Types
Selector.register_selector('has_type', has_type)
Selector.register_selector('raw_cells', is_raw)
Selector.register_selector('is_raw', is_raw)
Selector.register_selector('markdown_cells', is_markdown)
Selector.register_selector('is_markdown', is_markdown)
Selector.register_selector('code_cells', is_code)
Selector.register_selector('is_code', is_code)

# Slide cells
Selector.register_selector('has_slide_type', has_slide_type)
Selector.register_selector('is_new_slide', is_new_slide)
