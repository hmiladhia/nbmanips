from functools import partial

from nbmanips import Cell


class Selector:
    default_selectors = {}

    def __init__(self, selector, *args, **kwargs):
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


# Default Selectors
Selector.register_selector('contains', contains)
