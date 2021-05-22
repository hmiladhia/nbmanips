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
        if callable(selector):
            self._selector = partial(selector, *args, **kwargs)
        elif isinstance(selector, int):
            self._selector = lambda cell: cell.num == selector
        elif isinstance(selector, str):
            self._selector = partial(self.default_selectors[selector], *args, **kwargs)
        elif hasattr(selector, '__iter__'):
            selector = list(selector)
            type_ = kwargs.pop('type', 'and')
            assert not kwargs, "only 'type' keyword is allowed as keyword argument"
            if len(args) == len(selector):
                kwargs_list = args
            else:
                kwargs_list = args[0] if args else [{} for _ in selector]
            selector_list = [Selector(sel, **kwargs) for sel, kwargs in zip(selector, kwargs_list)]
            if type_ == 'and':
                self._selector = lambda cell: all(sel._selector(cell) for sel in selector_list)
            elif type_ == 'or':
                self._selector = lambda cell: any(sel._selector(cell) for sel in selector_list)
            else:
                raise ValueError(f'type can be "and" or "or": {type_}')
        elif isinstance(selector, slice):
            self._selector = self.__get_slice_selector(selector)
        else:
            raise ValueError(f'selector needs to be of type: (str, int, list, slice): {type(selector)}')

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

# Cell Types
Selector.register_selector('has_type', has_type)
Selector.register_selector('raw_cells', is_raw)
Selector.register_selector('markdown_cells', is_markdown)
Selector.register_selector('code_cells', is_code)

# Slide cells
Selector.register_selector('has_slide_type', has_slide_type)
