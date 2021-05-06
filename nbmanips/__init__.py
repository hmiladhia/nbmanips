import copy
import json


def read_ipynb(notebook_path):
    with open(notebook_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_ipynb(notebook, notebook_path):
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f)


class Notebook:
    def __init__(self, content):
        self.nb = copy.deepcopy(content)

    def __add__(self, other):
        # Copying the notebook
        nb = copy.copy(self.nb)

        # Concatenating the notebooks
        nb['cells'] = nb['cells'] + copy.copy(other.nb['cells'])
        return Notebook(nb)

    def replace(self, old, new):
        for i, cell in enumerate(self.nb['cells']):
            if old in '\n'.join(cell['source']):
                cell['source'] = [line.replace(old, new) for line in cell['source']]

    def erase(self, selector):
        for i, cell in enumerate(self.nb['cells']):
            if selector(cell):
                cell['source'] = []

    def delete(self, selector):
        self.nb['cells'] = [cell for cell in self.nb['cells'] if not selector(cell)]

    def keep(self, selector):
        self.nb['cells'] = [cell for cell in self.nb['cells'] if selector(cell)]

    def search(self, text, case=False):
        if not case:
            text = text.lower()

        for i, cell in enumerate(self.nb['cells']):
            if text in '\n'.join(cell['source']).lower():
                return i

    def search_all(self, text, case=False):
        if not case:
            text = text.lower()

        result = []
        for i, cell in enumerate(self.nb['cells']):
            if text in '\n'.join(cell['source']).lower():
                result.append(i)

        return result

    def to_ipynb(self, path):
        write_ipynb(self.nb, path)

    @classmethod
    def read_ipynb(cls, path):
        nb = read_ipynb(path)
        return Notebook(nb)
