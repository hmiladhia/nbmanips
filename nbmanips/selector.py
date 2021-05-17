from copy import copy
from functools import partial

from nbmanips import Cell


class Selector:
    default_selectors = {None: lambda cell: True}

    def __init__(self, selector, *args, **kwargs):
        self.slice = False
        self.list = False

        if callable(selector):
            assert not args  # TODO: add message
            self._selector = partial(selector, **kwargs)
        elif isinstance(selector, int):
            self.slice = slice(selector, *args, **kwargs)
        elif isinstance(selector, str):
            assert not args  # TODO: add message
            self._selector = partial(self.default_selectors[selector], **kwargs)
        elif isinstance(selector, list):
            if len(args) == len(selector):
                kwargs_list = args
            else:
                kwargs_list = args[0] if args else [{} for _ in selector]
            self.list = [Selector(sel, **kwgs) for sel, kwgs in zip(selector, kwargs_list)]
            # TODO: implement this
            raise NotImplemented("This feature is not implemented yet")
        elif isinstance(selector, slice):
            self.slice = selector
            start, stop, step = selector.start, selector.stop, selector.step
            self._selector = lambda cell: (cell.num < stop) and ((cell.num-start) % step == 0)

    def select(self, cell):
        return self._selector(cell)
        # return not result if self.neg else result

    def iter_cells(self, cells, neg=False):
        # TODO: move to select
        if self.slice:
            if neg:
                start, stop, step = self.slice.start, self.slice.stop, self.slice.step
                return filter(lambda i: i >= stop or ((i-start) % step), (Cell(c, i) for i, c in enumerate(cells)))
            else:
                return (Cell(cell, i) for i, cell in enumerate(cells[self.slice]))
        else:
            return filter(lambda cell: not self.select(cell) if neg else self.select(cell),
                          (Cell(cell, i) for i, cell in enumerate(cells)))

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


# Default Selectors
Selector.register_selector('contains', contains)
Selector.register_selector('has_type', has_type)
Selector.register_selector('raw_cells', is_raw)
Selector.register_selector('markdown_cells', is_markdown)
Selector.register_selector('code_cells', is_code)
