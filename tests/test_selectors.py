import pytest

from nbmanips import Notebook, Selector


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
    # (['has_output', 'contains'], (), 3), # TODO: add another error test for this
    (['has_output', 'contains'], ({'value': False}, {'text': '5'}), 2),
    (['has_output', 'contains'], ([{'value': False}, {'text': '5'}]), 2),
    (['has_output', 'contains'], ([{'value': True}, {'text': '5'}]), None),
    (['has_output', 'contains'], ([{'value': True}, {'text': 'a'}]), 3),
    (['has_output', 'contains'], ([{}, {'text': 'a'}]), 3),
    (['has_output', 'contains'], ({}, {'text': '5'}), None),
    (['has_output', 'contains'], ([True], ['a']), 3),
    (['has_output', 'contains'], ({'value': True}, ['a']), 3),
    (['has_output', 'contains'], ({'value': False}, ['5']), 2),
    (['has_output', 'contains'], ([True], (['hello'], {'case': True})), None),
    (['has_output', 'contains'], ([True], (('hello',), {'case': True})), None),
    (['has_output', 'contains'], ([True], (['hello'], {'case': False})), 1),
    (['has_output', 'contains'], ([True], (('hello',), {'case': False})), 1),
])
def test_list_selector_args(nb1, selector, args, expected):
    assert nb1.find(selector, *args) == expected


@pytest.mark.parametrize("slice_", [(0, 3), (1, 3), (1, 1), (0,), (1, 3, 2)])
def test_slice_selector(nb1, slice_: list):
    assert nb1.find_all(slice(*slice_)) == list(range(*slice_))


@pytest.mark.parametrize("value,expected", [(0, 0), (3, 3), (5, None)])
def test_int_selector(nb1, value, expected):
    assert nb1.find(value) == expected


def test_none_selector(nb1):
    assert nb1.find_all(None) == [i for i in range(len(nb1))]


def test_selector_selector(nb1):
    selector = Selector('contains', 'hello', case=False)
    assert nb1.find(selector) == 1


@pytest.mark.parametrize("output_type,expected",
                         [('text/plain', [1, 3])])
def test_has_output_type1(nb1, output_type, expected):
    assert nb1.find_all('has_output_type', output_type) == expected


# @pytest.mark.parametrize("output_type,expected",
#                          [('text/plain', [1, 3])])
# def test_has_output_type3(nb3, output_type, expected):
#     assert nb1.find_all('has_output_type', output_type) == expected
