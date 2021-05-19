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
            cell.cell['metadata'][tag_key] = tag_value

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

    def search(self, text, case=False, regex=False):
        sel = Selector('contains', text=text, case=case)
        if regex:
            raise NotImplemented("regex support isn't implemented yet")

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
        return Notebook(nb, get_ipynb_name(path))
