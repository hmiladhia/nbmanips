from nbmanips.notebook_base import NotebookBase
from nbmanips.notebook_mixins import SlideShowMixin
from nbmanips.notebook_mixins import ClassicNotebook
from nbmanips.notebook_mixins import ExportMixin
from nbmanips.utils import read_ipynb, get_ipynb_name


class Notebook(ClassicNotebook, ExportMixin, SlideShowMixin, NotebookBase):
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

        return self.select('contains', text=text, case=case, output=output).first()

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

        return self.select('contains', text=text, case=case, output=output).list()

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

        for cell in self.select('contains', text=old, case=case).iter_cells():
            cell.set_source([line.replace(old, new) for line in cell.get_source(text=False)])
            if first:
                break

    @classmethod
    def read_ipynb(cls, path):
        """
        Read ipynb file
        :param path: path to the ipynb file
        :return: Notebook object
        """
        nb = read_ipynb(path)
        return Notebook(nb, get_ipynb_name(path))
