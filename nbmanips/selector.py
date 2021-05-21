from functools import wraps

from nbmanips import Cell


def partial(func, *args, **keywords):
    @wraps(func)
    def new_func(*f_args, **f_keywords):
        new_keywords = {**f_keywords, **keywords}
        return func(*f_args, *args, **new_keywords)
    return new_func


class Selector:
    default_selectors = {None: lambda cell: True}

    def __init__(self, selector, *args, **kwargs):
        if callable(selector):
            assert not args  # TODO: add message
            self._selector = partial(selector, *args, **kwargs)
        elif isinstance(selector, int):
            self.slice = slice(selector, *args, **kwargs)
        elif isinstance(selector, str):
            self._selector = partial(self.default_selectors[selector], *args, **kwargs)
        elif isinstance(selector, list):
            if len(args) == len(selector):
                kwargs_list = args
            else:
                kwargs_list = args[0] if args else [{} for _ in selector]
            selector_list = [Selector(sel, **kwgs) for sel, kwgs in zip(selector, kwargs_list)]
            self._selector = lambda cell: all(sel.select(cell) for sel in selector_list)
        elif isinstance(selector, slice):
            start, stop, step = selector.start, selector.stop, selector.step
            self._selector = lambda cell: (cell.num < stop) and ((cell.num-start) % step == 0)

    def select(self, neg=False):
        if neg:
            return lambda cell: not self._selector(cell)
        else:
            return self._selector

    def iter_cells(self, cells, neg=False):
        return filter(self.select(neg), (Cell(cell, i) for i, cell in enumerate(cells)))

    @classmethod
    def register_selector(cls, key, selector):
        cls.default_selectors[key] = selector


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


def has_output(cell):
    return cell.output != ""


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
