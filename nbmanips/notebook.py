from nbmanips.notebook_base import NotebookBase
from nbmanips.notebook_mixins import (
    ClassicNotebook,
    ContentAnalysisMixin,
    ExportMixin,
    NotebookCellMetadata,
    NotebookMetadata,
    SlideShowMixin,
)


class Notebook(
    NotebookCellMetadata,
    SlideShowMixin,
    ClassicNotebook,
    ContentAnalysisMixin,
    ExportMixin,
    NotebookMetadata,
    NotebookBase,
):
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
        return self.select(
            'contains', text=text, case=case, output=output, regex=regex
        ).first()

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
        return self.select(
            'contains', text=text, case=case, output=output, regex=regex
        ).list()

    def replace(self, old, new, count=None, case=True, regex=False):
        """
        Replace matching text in the selected cells

        :param old: a string to replace in cell
        :param new: the replacement string
        :param count:
        :param case: True if the search is case sensitive
        :type case: default True
        :param regex: boolean whether to use regex or not
        """
        import re

        compiled_regex = re.compile(
            old if regex else re.escape(old), flags=0 if case else re.IGNORECASE
        )
        selection = self.select('contains', text=old, case=case, regex=regex)
        for n_cells, cell in enumerate(selection.iter_cells(), start=1):
            cell.source = compiled_regex.sub(new, cell.get_source())
            if count is not None and n_cells >= count:
                break


class IPYNB(Notebook):
    def __new__(cls, path, name=None):
        return Notebook.read_ipynb(path, name)


class DBC(Notebook):
    def __new__(cls, path, filename=None, encoding='utf-8', name=None):
        return Notebook.read_dbc(path, filename=filename, encoding=encoding, name=name)


class ZPLN(Notebook):
    def __new__(cls, path, name=None, encoding='utf-8'):
        return Notebook.read_zpln(path, encoding=encoding, name=name)
