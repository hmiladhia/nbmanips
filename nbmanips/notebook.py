from nbmanips.notebook_base import NotebookBase
from nbmanips.notebook_mixins import SlideShowMixin
from nbmanips.notebook_mixins import ClassicNotebook
from nbmanips.notebook_mixins import ExportMixin
from nbmanips.notebook_mixins import NotebookMetadata
from nbmanips.notebook_mixins import NotebookCellMetadata


class Notebook(NotebookCellMetadata, SlideShowMixin, ClassicNotebook, NotebookMetadata, ExportMixin, NotebookBase):
    def search(self, text, case=False, output=False, regex=False):
        """
        Return the number of the first cell containing the given text
        :param text: a string to find in cell
        :param case: True if the search is case sensitive
        :type case: default True
        :param output: True if you want the search in the output of the cell too
        :type output: default False
        :param regex: boolean whether to use regex or not
        :return:
        """
        return self.select('contains', text=text, case=case, output=output, regex=regex).first()

    def search_all(self, text, case=False, output=False, regex=False):
        """
        Return the numbers of the cells containing the given text

        :param text: a string to find in cell
        :param case: True if the search is case sensitive
        :type case: default True
        :param output: True if you want the search in the output of the cell too
        :type output: default False
        :param regex: boolean whether to use regex or not
        :return:
        """
        return self.select('contains', text=text, case=case, output=output, regex=regex).list()

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
