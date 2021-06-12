from copy import deepcopy

from nbmanips.notebook_base import NotebookBase
from nbmanips.notebook_mixins import SlideShowMixin
from nbmanips.notebook_mixins import ExportMixin
from nbmanips.utils import read_ipynb, write_ipynb, get_ipynb_name


class Notebook(ExportMixin, SlideShowMixin, NotebookBase):
    def replace(self, old, new, first=False, case=True):
        """
        Replace matching text in the selected cells

        :param old:
        :param new:
        :param first:
        :param case:
        """
        if not case:
            raise NotImplemented("case support is not implemented yet")

        for cell in self.iter_cells('contains', text=old, case=case):
            cell.set_source([line.replace(old, new) for line in cell.get_source(text=False)])
            if first:
                break

    def tag(self, tag_key, tag_value, selector, *args, **kwargs):
        """
        Add metadata to the selected cells
        :param tag_key:
        :param tag_value:
        :param selector:
        :param args:
        :param kwargs:
        """
        for cell in self.iter_cells(selector, *args, **kwargs):
            value = deepcopy(tag_value)
            if tag_key in cell.cell['metadata'] and isinstance(cell.cell['metadata'][tag_key], dict):
                cell.metadata[tag_key].update(value)
            else:
                cell.metadata[tag_key] = value

    def erase(self, selector, *args, **kwargs):
        """
        Erase the content of the selected cells
        :param selector:
        :param args:
        :param kwargs:
        """
        for cell in self.iter_cells(selector, *args, **kwargs):
            cell.set_source([])

    def delete(self, selector, *args, **kwargs):
        """
        Delete the selected cells
        :param selector:
        :param args:
        :param kwargs:
        """
        self._nb['cells'] = [cell.cell for cell in self.iter_neg_cells(selector, *args, **kwargs)]

    def keep(self, selector, *args, **kwargs):
        """
        Delete all the non-selected cells
        :param selector:
        :param args:
        :param kwargs:
        """
        self._nb['cells'] = [cell.cell for cell in self.iter_cells(selector, *args, **kwargs)]

    def find(self, selector, *args, **kwargs):
        """
        Return the number of the first selected cell
        :param selector:
        :param args:
        :param kwargs:
        :return:
        """
        for cell in self.iter_cells(selector, *args, **kwargs):
            return cell.num

    def find_all(self, selector, *args, **kwargs):
        """
        Return the numbers of the selected cells
        :param selector:
        :param args:
        :param kwargs:
        :return:
        """
        return [cell.num for cell in self.iter_cells(selector, *args, **kwargs)]

    def search(self, text, case=False, output=False, regex=False):
        """
        Return the number of the first cell containing the given text
        :param text:
        :param case:
        :param output:
        :param regex:
        :return:
        """
        if regex:
            raise NotImplemented("regex support isn't implemented yet")

        return self.find('contains', text=text, case=case, output=output)

    def search_all(self, text, case=False, output=False, regex=False):
        """
        Return the numbers of the cells containing the given text

        :param text:
        :param case:
        :param output:
        :param regex:
        :return:
        """
        if regex:
            raise NotImplemented("regex support isn't implemented yet")

        return self.find_all('contains', text=text, case=case, output=output)

    def show(self, selector=None, *args,  width=None, style='single', color=None,
             img_color=None, img_width=None, **kwargs):
        """
        Show the selected cells
        :param selector:
        :param args:
        :param width:
        :param style:
        :param color:
        :param img_color:
        :param img_width:
        :param kwargs:
        """
        print(self.to_str(selector, *args, width=width, style=style, color=color, img_color=img_color,
                          img_width=img_width, **kwargs))

    def to_ipynb(self, path):
        """
        Export to ipynb file
        :param path: target path
        """
        write_ipynb(self._nb, path)

    @classmethod
    def read_ipynb(cls, path):
        """
        Read ipynb file
        :param path: path to the ipynb file
        :return: Notebook object
        """
        nb = read_ipynb(path)
        return Notebook(nb, get_ipynb_name(path))
