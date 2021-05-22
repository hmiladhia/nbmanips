from copy import deepcopy

from nbmanips import read_ipynb, write_ipynb, get_ipynb_name
from nbmanips import Selector
from nbmanips import NotebookBase, SlideShowMixin


class Notebook(SlideShowMixin, NotebookBase):
    def replace(self, old, new, first=False, case=True):
        if not case:
            raise NotImplemented("case support is not implemented yet")

        sel = Selector('contains', text=old, case=case)
        for cell in sel.iter_cells(self.nb['cells']):
            cell.set_source([line.replace(old, new) for line in cell.get_source(text=False)])
            if first:
                break

    def tag(self, tag_key, tag_value, selector, *args, **kwargs):
        sel = Selector(selector, *args, **kwargs)
        for cell in sel.iter_cells(self.nb['cells']):
            value = deepcopy(tag_value)
            if tag_key in cell.cell['metadata'] and isinstance(cell.cell['metadata'][tag_key], dict):
                cell.cell['metadata'][tag_key].update(value)
            else:
                cell.cell['metadata'][tag_key] = value

    def erase(self, selector, *args, **kwargs):
        sel = Selector(selector, *args, **kwargs)
        for cell in sel.iter_cells(self.nb['cells']):
            cell.set_source([])

    def delete(self, selector, *args, **kwargs):
        selector = Selector(selector, *args, **kwargs)
        self.nb['cells'] = [cell.cell for cell in selector.iter_cells(self.nb['cells'], neg=True)]

    def keep(self, selector, *args, **kwargs):
        selector = Selector(selector, *args, **kwargs)
        self.nb['cells'] = [cell.cell for cell in selector.iter_cells(self.nb['cells'])]

    def find(self, selector, *args, **kwargs):
        sel = Selector(selector, *args, **kwargs)
        for cell in sel.iter_cells(self.nb['cells']):
            return cell.num

    def find_all(self, selector, *args, **kwargs):
        sel = Selector(selector, *args, **kwargs)
        return [cell.num for cell in sel.iter_cells(self.nb['cells'])]

    def search(self, text, case=False, output=False, regex=False):
        if regex:
            raise NotImplemented("regex support isn't implemented yet")

        return self.find('contains', text=text, case=case, output=output)

    def search_all(self, text, case=False, output=False, regex=False):
        if regex:
            raise NotImplemented("regex support isn't implemented yet")

        return self.find_all('contains', text=text, case=case, output=output)

    def to_ipynb(self, path):
        write_ipynb(self.nb, path)

    @classmethod
    def read_ipynb(cls, path):
        nb = read_ipynb(path)
        return Notebook(nb, get_ipynb_name(path))
