import re

from .notebook_base import NotebookBase
from .notebook_mixins import (
    ClassicNotebook,
    ContentAnalysisMixin,
    ExportMixin,
    NotebookCellMetadata,
    NotebookMetadata,
    SlideShowMixin,
)


def _get_regex(text, case=False, regex=False):
    if not regex:
        text = re.escape(text)

    flags = 0
    flags = (flags & ~re.IGNORECASE) if case else (flags | re.IGNORECASE)

    return re.compile(text, flags)


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

        if not regex:
            return self.select('contains', text=text, case=case, output=output).first()

        compiled_regex = _get_regex(text, case=case, regex=regex)
        return self.select('has_match', compiled_regex, output=output).first()

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

        if not regex:
            return self.select('contains', text=text, case=case, output=output).list()

        compiled_regex = _get_regex(text, case=case, regex=regex)
        return self.select('has_match', compiled_regex, output=output).list()

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

        compiled_regex = _get_regex(old, case=case, regex=regex)
        selection = self.select('has_match', compiled_regex)
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
