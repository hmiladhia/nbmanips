from nbmanips import read_ipynb, write_ipynb
from nbmanips import Selector
from nbmanips import NotebookBase, SlideShowMixin


class Notebook(SlideShowMixin, NotebookBase):
    def replace(self, old, new):
        sel = Selector(('contains', {'text': old}))
        for cell in sel.iter_cells(self.nb['cells']):
            cell.set_source([line.replace(old, new) for line in cell.get_source(text=False)])

    def tag(self, tag_key, tag_value, selector, *args, **kwargs):
        sel = Selector(selector, *args, **kwargs)
        for cell in sel.iter_cells(self.nb['cells']):
            cell.cell['metadata'][tag_key] = tag_value

    def erase(self, selector, *args, **kwargs):
        sel = Selector(selector, *args, **kwargs)
        for cell in sel.iter_cells(self.nb['cells']):
            cell.set_source([])

    def delete(self, selector, *args, **kwargs):
        self.nb['cells'] = [cell.cell for cell in ~Selector(selector, *args, **kwargs).iter_cells(self.nb['cells'])]

    def keep(self, selector, *args, **kwargs):
        self.nb['cells'] = [cell.cell for cell in Selector(selector).iter_cells(self.nb['cells'])]

    def search(self, text, case=False):
        sel = Selector(('contains', dict(text=text, case=case)))

        for cell in sel.iter_cells(self.nb['cells']):
            return cell.num

    def search_all(self, text, case=False):
        sel = Selector(('contains', dict(text=text, case=case)))
        return [cell.num for cell in sel.iter_cells(self.nb['cells'])]

    def to_ipynb(self, path):
        write_ipynb(self.nb, path)

    @classmethod
    def read_ipynb(cls, path):
        nb = read_ipynb(path)
        return Notebook(nb)
