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


def test_read(nb1):
    assert len(nb1.raw_nb['cells']) == 4


def test_name(nb1):
    assert nb1.name == 'nb1'


def test_len_empty():
    assert len(Notebook({})) == 0


def test_len(nb2):
    assert len(nb2) == 5


def test_count_all(nb2):
    assert len(nb2) == nb2.count()


def test_count(nb2):
    assert nb2.select('contains', 'a').count() == 2
    assert nb2.select('contains', 'hello', case=False).count()


@pytest.mark.parametrize("search_term,case,output,expected", [
    ('b', False, False, None),
    ('Hello', False, False, 1),
    ('hello', False, False, 1),
    ('hello', True, False, None),
    ('a', True, False, 0),
    ('a ', True, False, 2),
    ('125', True, False, None),
    ('125', True, True, 3),
])
def test_search(nb1, search_term, case, output, expected):
    # TODO: Test regexes
    assert nb1.search(search_term, case=case, output=output) == expected


@pytest.mark.parametrize("search_term,case,output,expected", [
    ('b', False, False, []),
    ('Hello', False, False, [1]),
    ('hello', False, False, [1]),
    ('hello', True, False, []),
    ('a', True, False, [0, 2, 3]),
    ('a ', True, False, [2]),
    ('125', True, False, []),
    ('125', True, True, [3]),
])
def test_search_all(nb1, search_term, case, output, expected):
    assert nb1.search_all(search_term, case=case, output=output) == expected


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


@pytest.mark.parametrize("selector, selector_kwargs, search_term, expected", [
    ('contains', {'text': 'Hello'}, 'World', []),
    ('contains', {'text': 'Hllo'}, 'World', [1]),
    ('contains', {'text': 'a '}, 'a', [0, 3]),
])
def test_erase(nb0, selector, selector_kwargs, search_term, expected):
    nb0.select(selector, **selector_kwargs).erase()
    assert nb0.search_all(search_term, case=True) == expected
    assert len(nb0) == 4


@pytest.mark.parametrize("selector, selector_kwargs, search_term, expected, expected_length", [
    ('contains', {'text': 'Hello'}, 'World', [], 3),
    ('contains', {'text': 'Hllo'}, 'World', [1], 4),
    ('contains', {'text': 'a '}, 'a', [0, 2], 3),
])
def test_delete(nb0, selector, selector_kwargs, search_term, expected, expected_length):
    nb0.select(selector, **selector_kwargs).delete()
    assert nb0.search_all(search_term, case=True) == expected
    assert len(nb0) == expected_length


@pytest.mark.parametrize("selector, selector_kwargs, search_term, expected, expected_length", [
    ('contains', {'text': 'Hello'}, 'World', [0], 1),
    ('contains', {'text': 'Hllo'}, 'World', [], 0),
    ('contains', {'text': 'a'}, 'a', [0, 1, 2], 3),
    ('contains', {'text': 'a '}, 'a', [0], 1),
])
def test_keep(nb0, selector, selector_kwargs, search_term, expected, expected_length):
    nb0.select(selector, **selector_kwargs).keep()
    assert nb0.search_all(search_term, case=True) == expected
    assert len(nb0) == expected_length


def test_tag(nb0):
    nb0.select(lambda cell: cell.num in {0, 1, 2}).update_cell_metadata('test', {"key": "value"})
    nb0.select(lambda cell: cell.num == 1).update_cell_metadata('test', {"key": "new_value"})
    assert nb0.cells[1]['metadata']['test']['key'] == "new_value"
    assert nb0.cells[0]['metadata']['test']['key'] == "value"


# @pytest.mark.parametrize("slice_", [(0, 3), (1, 3), (1, 1), (0,), (1, 3, 2)])
def test_get_item_selector(nb1):
    assert nb1[0:3].list() == list(range(0, 3))
    assert nb1[1:3].list() == list(range(1, 3))
    assert nb1[1:1].list() == list(range(1, 1))
    assert nb1[:0].list() == list(range(0))
    assert nb1[1:3:2].list() == list(range(1, 3, 2))
    assert nb1['has_output'].first() == 1
    assert nb1['contains', 'hello', False].first() == 1


@pytest.mark.parametrize("selector,args,expected", [
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
def test_list_selector_chaining(nb1, selector, args, expected):
    selection = nb1.select(None)
    for sel, sel_args in zip(selector, args):
        if isinstance(sel_args, dict):
            selection = selection.select(sel, **sel_args)
        elif isinstance(sel_args, tuple) and len(sel_args) == 2:
            selection = selection.select(sel, *sel_args[0], **sel_args[1])
        else:
            selection = selection.select(sel, *sel_args)
    assert selection.first() == expected
    assert selection.first() == nb1.select(selector, *args).first()


def test_nb_multiply(nb1):
    result_nb = nb1 * 3
    assert isinstance(result_nb, Notebook)
    assert len(nb1)*3 == len(result_nb)


def test_nb_add(nb1, nb2):
    result_nb = nb1 + nb2
    assert isinstance(result_nb, Notebook)
    assert len(nb1) + len(nb2) == len(result_nb)

# def test_selectors(nb0, selector, selector_kwargs):
#     assert False
# def test_get_item(nb1):
#     assert nb1['cells'] == nb1.nb['cells']
#
# def test_tag(self, tag_key, tag_value, selector, *args, **kwargs):
#     ...
#
# def to_ipynb(self, path):
#     write_ipynb(self.nb, path)

