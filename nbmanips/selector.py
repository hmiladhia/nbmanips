from functools import wraps

from nbmanips import Cell


def partial(func, *args, **keywords):
    @wraps(func)
    def new_func(*f_args, **f_keywords):
        new_keywords = {**f_keywords, **keywords}
        return func(*f_args, *args, **new_keywords)
    return new_func


class Selector:
    default_selectors = {}

    def __init__(self, selector, *args, **kwargs):
        self._selector = self._get_selector(selector, *args, **kwargs)

    def get_selector(self, neg=False) -> callable:
        if neg:
            return lambda cell: not self._selector(cell)
        else:
            return self._selector

    def iter_cells(self, cells, neg=False):
        return filter(self.get_selector(neg), (Cell(cell, i) for i, cell in enumerate(cells)))

    @classmethod
    def register_selector(cls, key, selector):
        cls.default_selectors[key] = selector

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
            return selector.get_selector()
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
        selector_list = []
        if start is not None:
            selector_list.append(lambda cell: cell.num >= start)
        if stop is not None:
            selector_list.append(lambda cell: cell.num < stop)
        if step:
            selector_list.append(lambda cell: (cell.num - start) % step == 0)
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


def contains(cell, text, case=True, output=False):
    return cell.contains(text, case=case, output=output)


def has_type(cell, type):
    return cell.type == type


def is_code(cell):
    return has_type(cell, 'code')


def is_markdown(cell):
    return has_type(cell, 'markdown')


def is_raw(cell):
    return has_type(cell, 'raw')


def has_output(cell, value=True):
    return (cell.output != "") == value


def is_empty(cell):
    return cell.source == '' and has_output(cell, False)


def has_slide_type(cell, slide_type):
    if isinstance(slide_type, str):
        slide_type = {slide_type}

    return all(['slideshow' in cell.metadata,
                'slide_type' in cell.metadata['slideshow'],
                cell.metadata['slideshow']['slide_type'] in slide_type
                ])


# Default Selectors
Selector.register_selector('contains', contains)
Selector.register_selector('has_output', has_output)
Selector.register_selector('empty', is_empty)

# Cell Types
Selector.register_selector('has_type', has_type)
Selector.register_selector('raw_cells', is_raw)
Selector.register_selector('markdown_cells', is_markdown)
Selector.register_selector('code_cells', is_code)

# Slide cells
Selector.register_selector('has_slide_type', has_slide_type)
