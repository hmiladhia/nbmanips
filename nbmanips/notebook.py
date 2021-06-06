from copy import deepcopy

from nbmanips.notebook_base import NotebookBase
from nbmanips.notebook_mixins import SlideShowMixin
from nbmanips.notebook_mixins import ExportMixin
from nbmanips.utils import read_ipynb, write_ipynb, get_ipynb_name


class Notebook(ExportMixin, SlideShowMixin, NotebookBase):
    def replace(self, old, new, first=False, case=True):
        if not case:
            raise NotImplemented("case support is not implemented yet")

        for cell in self.iter_cells('contains', text=old, case=case):
            cell.set_source([line.replace(old, new) for line in cell.get_source(text=False)])
            if first:
                break

    def tag(self, tag_key, tag_value, selector, *args, **kwargs):
        for cell in self.iter_cells(selector, *args, **kwargs):
            value = deepcopy(tag_value)
            if tag_key in cell.cell['metadata'] and isinstance(cell.cell['metadata'][tag_key], dict):
                cell.metadata[tag_key].update(value)
            else:
                cell.metadata[tag_key] = value

    def erase(self, selector, *args, **kwargs):
        for cell in self.iter_cells(selector, *args, **kwargs):
            cell.set_source([])

    def delete(self, selector, *args, **kwargs):
        self._nb['cells'] = [cell.cell for cell in self.iter_neg_cells(selector, *args, **kwargs)]

    def keep(self, selector, *args, **kwargs):
        self._nb['cells'] = [cell.cell for cell in self.iter_cells(selector, *args, **kwargs)]

    def find(self, selector, *args, **kwargs):
        for cell in self.iter_cells(selector, *args, **kwargs):
            return cell.num

    def find_all(self, selector, *args, **kwargs):
        return [cell.num for cell in self.iter_cells(selector, *args, **kwargs)]

    def search(self, text, case=False, output=False, regex=False):
        if regex:
            raise NotImplemented("regex support isn't implemented yet")

        return self.find('contains', text=text, case=case, output=output)

    def search_all(self, text, case=False, output=False, regex=False):
        if regex:
            raise NotImplemented("regex support isn't implemented yet")

        return self.find_all('contains', text=text, case=case, output=output)

    def show(self, selector=None, *args,  width=None, style='single', color=None,
             img_color=None, img_width=None, **kwargs):
        print(self.to_str(selector, *args, width=width, style=style, color=color, img_color=img_color,
                          img_width=img_width, **kwargs))

    def to_ipynb(self, path):
        write_ipynb(self._nb, path)

    @classmethod
    def read_ipynb(cls, path):
        nb = read_ipynb(path)
        return Notebook(nb, get_ipynb_name(path))
