import copy

from nbmanips import read_ipynb, write_ipynb
from nbmanips import Selector


class Notebook:
    def __init__(self, content):
        self.nb = copy.deepcopy(content)

    def __add__(self, other):
        # Copying the notebook
        nb = copy.copy(self.nb)

        # Concatenating the notebooks
        nb['cells'] = nb['cells'] + copy.copy(other.nb['cells'])
        return Notebook(nb)

    def replace(self, old, new):
        sel = Selector(lambda cell: old in cell.get_source())
        for cell in sel.iter_cells(self.nb['cells']):
            cell.set_source([line.replace(old, new) for line in cell.get_source(text=False)])

    def tag(self, tag_key, tag_value, selector):
        for i, cell in enumerate(self.nb['cells']):
            if selector(cell):
                cell['metadata'][tag_key] = tag_value

    def erase(self, selector):
        sel = Selector(selector)
        for cell in sel.iter_cells(self.nb['cells']):
            cell.set_source([])

    def delete(self, selector):
        # TODO
        self.nb['cells'] = [cell for cell in self.nb['cells'] if not selector(cell)]

    def keep(self, selector):
        self.nb['cells'] = [cell.cell for cell in Selector(selector).iter_cells(self.nb['cells'])]

    def search(self, text, case=False):
        sel = Selector('contains', text=text, case=case)

        for cell in sel.iter_cells(self.nb['cells']):
            return cell.num

    def search_all(self, text, case=False):
        sel = Selector('contains', text=text, case=case)
        return [cell.num for cell in sel.iter_cells(self.nb['cells'])]

    def to_ipynb(self, path):
        write_ipynb(self.nb, path)

    @classmethod
    def read_ipynb(cls, path):
        nb = read_ipynb(path)
        return Notebook(nb)
