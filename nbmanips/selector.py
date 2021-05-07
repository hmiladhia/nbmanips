from functools import partial

from nbmanips import Cell


class Selector:
    default_selectors = {None: lambda cell: True}

    def __init__(self, selector=None, *args, **kwargs):
        if callable(selector):
            self._selector = selector
        else:
            self._selector = partial(self.default_selectors[selector], *args, **kwargs)

    def select(self, cell):
        return self._selector(cell)

    def iter_cells(self, cells):
        # return (Cell(cell, i) for i, cell in enumerate(cells) if self.select(cell))
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
Selector.register_selector('is_raw', is_raw)
Selector.register_selector('is_markdown', is_markdown)
Selector.register_selector('is_code', is_code)
