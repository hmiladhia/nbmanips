import re

from nbmanips.notebook_base import NotebookBase
from nbmanips.notebook_mixins import SlideShowMixin
from nbmanips.notebook_mixins import ClassicNotebook
from nbmanips.notebook_mixins import ExportMixin
from nbmanips.notebook_mixins import NotebookMetadata
from nbmanips.notebook_mixins import NotebookCellMetadata
from nbmanips.notebook_mixins import ContentAnalysisMixin


class Notebook(
    NotebookCellMetadata,
    SlideShowMixin,
    ClassicNotebook,
    ContentAnalysisMixin,
    ExportMixin,
    NotebookMetadata,
    NotebookBase
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

        compiled_regex = re.compile(old if regex else re.escape(old), flags=0 if case else re.IGNORECASE)
        selection = self.select('contains', text=old, case=case, regex=regex)
        for n_cells, cell in enumerate(selection.iter_cells(), start=1):
            cell.source = compiled_regex.sub(new, cell.get_source())
            if count is not None and n_cells >= count:
                break

    def burn_attachments(self, relative_path=None, html=True):
        from functools import partial
        from nbmanips.utils import burn_attachment_md
        from nbmanips.utils import burn_attachment_html
        from nbmanips.utils import get_relative_path

        relative_path = get_relative_path(self, relative_path)

        compiled_md_regex = re.compile(r'!\[(?P<alt_text>.*?)]\((?P<PATH>.*?)\)')
        compiled_html_regex = re.compile(r'<img\s(?P<PREFIX>.*?)src\s*=\s*"(?P<PATH>.*?)"(?P<SUFFIX>.*?)>')
        selection = self.select('markdown_cells')
        for cell in selection.iter_cells():
            # replace markdown
            rep_func = partial(burn_attachment_md, cell=cell, relative_path=relative_path)
            cell.source = compiled_md_regex.sub(rep_func, cell.get_source())

            if not html:
                continue

            # replace html
            rep_func = partial(burn_attachment_html, cell=cell, relative_path=relative_path)
            cell.source = compiled_html_regex.sub(rep_func, cell.get_source())


class IPYNB(Notebook):
    def __new__(cls, path, name=None):
        return Notebook.read_ipynb(path, name)


class DBC(Notebook):
    def __new__(cls, path, filename=None, encoding='utf-8', name=None):
        return Notebook.read_dbc(path, filename=filename, encoding=encoding, name=name)


class ZPLN(Notebook):
    def __new__(cls, path, name=None, encoding='utf-8'):
        return Notebook.read_zpln(path, encoding=encoding, name=name)
