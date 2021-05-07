from functools import partial

from nbmanips import Cell


class Selector:
    default_selectors = {None: lambda cell: True}

    def __init__(self, selector=None, neg=False):
        self.neg = neg
        self.is_slice = False
        if callable(selector):
            self._selector = selector
        elif isinstance(selector, str):
            self._selector = self.default_selectors[selector]
        elif isinstance(selector, tuple):
            self._selector = partial(self.default_selectors[selector[0]], **selector[1])
        elif isinstance(selector, slice):
            self.is_slice = True
            self._selector = selector

    def select(self, cell):
        result = self._selector(cell)
        return not result if self.neg else result

    def iter_cells(self, cells):
        if self.is_slice:
            return (Cell(cell, i) for i, cell in enumerate(cells[self._selector]))
        else:
            for i, cell in enumerate(cells):
                cell = Cell(cell, i)
                if self.select(cell):
                    yield cell

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
Selector.register_selector('markdown_cels', is_markdown)
Selector.register_selector('code_cells', is_code)
