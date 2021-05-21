import pytest

from nbmanips import Notebook


@pytest.fixture(scope='function')
def nb0():
    return Notebook.read_ipynb('test_files/nb1.ipynb')


@pytest.fixture(scope='session')
def nb1():
    return Notebook.read_ipynb('test_files/nb1.ipynb')


@pytest.fixture(scope='session')
def nb2():
    return Notebook.read_ipynb('test_files/nb2.ipynb')


@pytest.fixture(scope='session')
def nb3():
    return Notebook.read_ipynb('test_files/nb3.ipynb')


@pytest.mark.parametrize("cell_num, expected", [
    (0, False), (1, False), (2, True), (3, True), (4, True),
    (5, False), (6, True), (7, True), (8, False),
])
def test_has_output(nb3, cell_num, expected):
    from nbmanips.selector import has_output
    from nbmanips import Cell

    cell = Cell(nb3.cells[cell_num], cell_num)
    assert has_output(cell) == expected


@pytest.mark.parametrize("selector,args,expected", [
    ('has_output', (), 1),
    ('contains', ('Hello',), 1),
    ('contains', ('hello', False), 1),  # case=False
    ('contains', ('hello', True), None),  # case=True
])
def test_selector_args(nb1, selector, args, expected):
    assert nb1.find(selector, *args) == expected


@pytest.mark.parametrize("selector,args,expected", [
    # (['has_output', 'contains'], (), 3),
    (['has_output', 'contains'], ({'value': False}, {'text': '5'}), 2),
    (['has_output', 'contains'], ([{'value': False}, {'text': '5'}]), 2),
    (['has_output', 'contains'], ([{'value': True}, {'text': '5'}]), None),
    (['has_output', 'contains'], ([{'value': True}, {'text': 'a'}]), 3),
    (['has_output', 'contains'], ([{}, {'text': 'a'}]), 3),
    (['has_output', 'contains'], ({}, {'text': '5'}), None),
    # (['has_output', 'contains'], ([True], ['a']), 3),
])
def test_list_selector_args(nb1, selector, args, expected):
    assert nb1.find(selector, *args) == expected
