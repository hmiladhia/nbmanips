import pytest

from nbmanips import Notebook


@pytest.fixture(scope='function')
def nb0():
    return Notebook.read_ipynb('test_files/nb1.ipynb')


@pytest.fixture(scope='session')
def nb1():
    return Notebook.read_ipynb('test_files/nb1.ipynb')


# @pytest.fixture(autouse=True)
# def dmail(nb1):
#     with Email(**config.email) as dmail:
#         mocker.patch.object(dmail.server, 'sendmail')
#         yield dmail


def test_read(nb1):
    assert len(nb1.nb['cells']) == 4


@pytest.mark.parametrize("search_term,case,expected", [
    ('b', False, None),
    ('Hello', False, 1),
    ('hello', False, 1),
    ('hello', True, None),
    ('a', True, 0),
    ('a ', True, 2),
])
def test_search(nb1, search_term, case, expected):
    # TODO: Test regexes
    # TODO: Test output
    assert nb1.search(search_term, case=case) == expected


@pytest.mark.parametrize("old, new, case, first, expected_old, expected_new", [
    ('jupyter', 'Test', True, False, [], []),
    ('Hello', 'Test', True, False, [], [1]),
    ('hello', 'Test', True, False, [], []),
    ('a', 'Test', True, False, [], [0, 2, 3]),
    ('a', 'Test', True, True, [2, 3], [0]),
])
def test_replace(nb0, old, new, case, first, expected_old, expected_new):
    nb0.replace(old, new, first=first, case=case)
    assert nb0.search_all(old, case=case) == expected_old
    assert nb0.search_all(new, case=True) == expected_new



@pytest.mark.parametrize("search_term,case,expected", [
    ('b', False, []),
    ('Hello', False, [1]),
    ('hello', False, [1]),
    ('hello', True, []),
    ('a', True, [0, 2, 3]),
    ('a ', True, [2]),
])
def test_search_all(nb1, search_term, case, expected):
    assert nb1.search_all(search_term, case=case) == expected



# def test_get_item(nb1):
#     assert nb1['cells'] == nb1.nb['cells']

# def replace(self, old, new):
#     sel = Selector('contains', text=old)
#     for cell in sel.iter_cells(self.nb['cells']):
#         cell.set_source([line.replace(old, new) for line in cell.get_source(text=False)])
#
# def tag(self, tag_key, tag_value, selector, *args, **kwargs):
#     sel = Selector(selector, *args, **kwargs)
#     for cell in sel.iter_cells(self.nb['cells']):
#         cell.cell['metadata'][tag_key] = tag_value
#
# def erase(self, selector, *args, **kwargs):
#     sel = Selector(selector, *args, **kwargs)
#     for cell in sel.iter_cells(self.nb['cells']):
#         cell.set_source([])
#
# def delete(self, selector, *args, **kwargs):
#     selector = Selector(selector, *args, **kwargs)
#     self.nb['cells'] = [cell.cell for cell in selector.iter_cells(self.nb['cells'], neg=True)]
#
# def keep(self, selector, *args, **kwargs):
#     selector = Selector(selector, *args, **kwargs)
#     self.nb['cells'] = [cell.cell for cell in selector.iter_cells(self.nb['cells'])]
#
#
# def to_ipynb(self, path):
#     write_ipynb(self.nb, path)
#
# @classmethod
# def read_ipynb(cls, path):
#     nb = read_ipynb(path)
#     return Notebook(nb)
