import copy
import json

try:
    import nbformat
except ImportError:
    nbformat = None

try:
    import nbconvert
except ImportError:
    nbconvert = None

from nbmanips.cell import Cell
from nbmanips.selector import Selector


class NotebookBase:
    def __init__(self, content, name=None):
        self._nb = copy.deepcopy(content)
        self.name = name

    def __add__(self, other: 'NotebookBase'):
        # Copying the notebook
        nb = copy.deepcopy(self._nb)

        # Concatenating the notebooks
        nb['cells'] = nb['cells'] + other._nb['cells']
        return self.__class__(nb)

    def __getitem__(self, item):
        return self._nb[item]

    def __setitem__(self, item, value):
        self._nb[item] = value

    def __len__(self):
        if self._nb is None or 'cells' not in self._nb:
            return 0
        return len(self._nb['cells'])

    def __repr__(self):
        if self.name:
            return f'<Notebook "{self.name}">'
        else:
            return "<Notebook>"

    def __str__(self):
        return '\n'.join(str(Cell(cell, i, self._nb)) for i, cell in enumerate(self.cells))

    def iter_cells(self, selector=None, *args, **kwargs):
        return Selector(selector, *args, **kwargs).iter_cells(self._nb)

    def iter_neg_cells(self, selector, *args, **kwargs):
        return Selector(selector, *args, **kwargs).iter_cells(self._nb, neg=True)

    def to_notebook_node(self):
        if nbformat:
            version = self._nb.get('nbformat', 4)
            return nbformat.reads(json.dumps(self._nb), as_version=version)
        else:
            raise ModuleNotFoundError('You need to pip install nbformat to get NotebookNode object')

    def to_html(self, path, exclude_code_cell=False, exclude_markdown=False, exclude_raw=False,
                exclude_unknown=False, exclude_input=False, exclude_output=False, **kwargs):
        """
        :param path:
        :param exclude_code_cell: This allows you to exclude code cells from all templates if set to True.
        :param exclude_markdown: This allows you to exclude markdown cells from all templates if set to True.
        :param exclude_raw: This allows you to exclude raw cells from all templates if set to True.
        :param exclude_unknown: This allows you to exclude unknown cells from all templates if set to True.
        :param exclude_input: This allows you to exclude input prompts from all templates if set to True.
        :param exclude_output: This allows you to exclude code cell outputs from all templates if set to True.
        :param kwargs: exclude_input_prompt, exclude_output_prompt, ...
        """
        notebook_node = self.to_notebook_node()
        exporter = nbconvert.HTMLExporter(exclude_code_cell=exclude_code_cell,
                                          exclude_markdown=exclude_markdown,
                                          exclude_raw=exclude_raw,
                                          exclude_unknown=exclude_unknown,
                                          exclude_input=exclude_input,
                                          exclude_output=exclude_output,
                                          **kwargs)

        (body, resources) = exporter.from_notebook_node(notebook_node)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(body)

    @property
    def cells(self):
        return self._nb['cells']
