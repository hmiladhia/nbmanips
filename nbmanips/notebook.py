import re

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

        compiled_regex = re.compile(
            old if regex else re.escape(old), flags=0 if case else re.IGNORECASE
        )
        selection = self.select('contains', text=old, case=case, regex=regex)
        for n_cells, cell in enumerate(selection.iter_cells(), start=1):
            cell.source = compiled_regex.sub(new, cell.get_source())
            if count is not None and n_cells >= count:
                break

    def burn_attachments(self, assets_path=None, html=True):
        from functools import partial

        from nbmanips.utils import (
            burn_attachment_html,
            burn_attachment_md,
            get_assets_path,
        )

        assets_path = get_assets_path(self, assets_path)
        compiled_md_regex = re.compile(r'!\[(?P<ALT_TEXT>.*?)]\((?P<PATH>.*?)\)')
        compiled_html_regex = re.compile(
            r'<img\s(?P<PREFIX>.*?)'
            r'src\s*=\s*\"?(?P<PATH>(?<=\")[^\"]*(?=\")|(?:[^\"\s]|(?<=\\)\s)*)\"?'
            r'(?P<SUFFIX>.*?)>'
        )
        for cell in self.select('markdown_cells').iter_cells():
            # replace markdown
            rep_func = partial(
                burn_attachment_md, cell=cell, assets_path=assets_path
            )
            cell.source = compiled_md_regex.sub(rep_func, cell.get_source())

            if not html:
                continue

            # replace html
            rep_func = partial(
                burn_attachment_html, cell=cell, assets_path=assets_path
            )
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

