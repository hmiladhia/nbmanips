import nbformat
import pytest

from nbmanips import Notebook


@pytest.fixture(scope='function')
def nb1_0():
    return Notebook.read_ipynb('test_files/nb1.ipynb')


@pytest.fixture(scope='function')
def nb3_0():
    return Notebook.read_ipynb('test_files/nb3.ipynb')


@pytest.fixture(scope='session')
def nb1():
    return Notebook.read_ipynb('test_files/nb1.ipynb')


@pytest.fixture(scope='session')
def nb2():
    return Notebook.read_ipynb('test_files/nb2.ipynb')


@pytest.fixture(scope='session')
def nb3():
    """Notebook with images"""
    return Notebook.read_ipynb('test_files/nb3.ipynb')


@pytest.fixture(scope='session')
def nb5():
    """Notebook in version 4.5"""
    return Notebook.read_ipynb('test_files/nb5.ipynb')


def test_read(nb1):
    assert len(nb1.raw_nb['cells']) == 4


def test_name(nb1):
    assert nb1.name == 'nb1'


def test_len_empty():
    assert len(Notebook({
        'cells': [],
        'nbformat': 4,
        'nbformat_minor': 0,
        'metadata': {},
    })) == 0


def test_schema():
    from jsonschema.exceptions import ValidationError

    with pytest.raises(ValidationError):
        Notebook({})

    with pytest.raises(ValueError):
        Notebook('file.ipynb')


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
    assert nb1.search(search_term, case=case, output=output) == expected


@pytest.mark.parametrize("search_term,case,output,expected", [
    ('b', False, False, None),
    (r'H\w+o', False, False, 1),
    (r'h\w+o', False, False, 1),
    (r'h\w+o', True, False, None),
    ('a', True, False, 0),
    ('a ', True, False, 2),
    ('125', True, False, None),
    ('125', True, True, 3),
])
def test_regex_search(nb1, search_term, case, output, expected):
    assert nb1.search(search_term, case=case, output=output, regex=True) == expected


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


@pytest.mark.parametrize("old, new, case, count, regex, expected_old, expected_new", [
    ('jupyter', 'Test', True, None, False, [], []),
    ('Hello', 'Test', True, None, False, [], [1]),
    ('hello', 'Test', True, None, False, [], []),
    ('a', 'Test', True, None, False, [], [0, 2, 3]),
    ('a', 'Test', True, 1, False, [2, 3], [0]),
    ('a', 'Test', True, 2, False, [3], [0, 2]),
    ('A', 'Test', False, None, False, [], [0, 2, 3]),
    ('A', 'Test', True, None, False, [], []),
    (r'[A-Za-z_]\w*\s*=\s*\d+\s*[+-\/*]\s*\d+', 'OPERATION', True, None, True, [], [2]),
])
def test_replace(nb1_0, old, new, case, count, regex, expected_old, expected_new):
    nb1_0.replace(old, new, count=count, case=case, regex=regex)
    assert nb1_0.search_all(old, case=case) == expected_old
    assert nb1_0.search_all(new, case=True) == expected_new


@pytest.mark.parametrize("selector, selector_kwargs, search_term, expected", [
    ('contains', {'text': 'Hello'}, 'World', []),
    ('contains', {'text': 'Hllo'}, 'World', [1]),
    ('contains', {'text': 'a '}, 'a', [0, 3]),
])
def test_erase(nb1_0, selector, selector_kwargs, search_term, expected):
    nb1_0.select(selector, **selector_kwargs).erase()
    assert nb1_0.search_all(search_term, case=True) == expected
    assert len(nb1_0) == 4


def test_erase_output(nb3_0):
    assert nb3_0.select('has_output_type', 'image/png').count() == 2
    nb3_0.erase_output('image/png')
    assert nb3_0.select('has_output_type', 'image/png').count() == 0


@pytest.mark.parametrize("selector, selector_kwargs, search_term, expected, expected_length", [
    ('contains', {'text': 'Hello'}, 'World', [], 3),
    ('contains', {'text': 'Hllo'}, 'World', [1], 4),
    ('contains', {'text': 'a '}, 'a', [0, 2], 3),
])
def test_delete(nb1_0, selector, selector_kwargs, search_term, expected, expected_length):
    nb1_0.select(selector, **selector_kwargs).delete()
    assert nb1_0.search_all(search_term, case=True) == expected
    assert len(nb1_0) == expected_length


@pytest.mark.parametrize("selector, selector_kwargs, search_term, expected, expected_length", [
    ('contains', {'text': 'Hello'}, 'World', [0], 1),
    ('contains', {'text': 'Hllo'}, 'World', [], 0),
    ('contains', {'text': 'a'}, 'a', [0, 1, 2], 3),
    ('contains', {'text': 'a '}, 'a', [0], 1),
])
def test_keep(nb1_0, selector, selector_kwargs, search_term, expected, expected_length):
    nb1_0.select(selector, **selector_kwargs).keep()
    assert nb1_0.search_all(search_term, case=True) == expected
    assert len(nb1_0) == expected_length


def test_tag(nb1_0):
    nb1_0.select(lambda cell: cell.num in {0, 1, 2}).update_cell_metadata('test', {"key": "value"})
    nb1_0.select(lambda cell: cell.num == 1).update_cell_metadata('test', {"key": "new_value"})
    assert nb1_0.cells[1]['metadata']['test']['key'] == "new_value"
    assert nb1_0.cells[0]['metadata']['test']['key'] == "value"


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


def test_nb_multiply(nb5):
    result_nb = nb5 * 3
    nbformat.validate(result_nb.raw_nb)
    assert isinstance(result_nb, Notebook)
    assert len(nb5) * 3 == len(result_nb)


def test_nb_add(nb1, nb2):
    result_nb = nb1 + nb2
    nbformat.validate(result_nb.raw_nb)
    assert isinstance(result_nb, Notebook)
    assert len(nb1) + len(nb2) == len(result_nb)


def test_nb_add_45(nb1, nb5):
    result_nb = nb5 + nb1 + nb5
    nbformat.validate(result_nb.raw_nb)
    assert isinstance(result_nb, Notebook)
    assert len(nb1) + 2*len(nb5) == len(result_nb)


def test_apply(nb1_0):
    def replace(cell):
        if 'Hello' in cell.get_source():
            return None
        cell.set_source(cell.get_source().replace('a', 'b').split('\n'))
        return cell
    sel = nb1_0.create_selector('contains', '=') | nb1_0.create_selector('contains', 'H')
    nb1_0.select(sel).apply(replace)
    assert nb1_0.select('contains', 'b').list() == [1]
    assert nb1_0.select('contains', 'a').list() == [0, 2]
    assert nb1_0.select('contains', 'Hello').list() == []


def test_cover_auto_slide(nb3_0):
    nb3_0.auto_slide()
    assert nb3_0.select('has_slide_type', 'slide').list() == []
    assert nb3_0.select('has_slide_type', 'subslide').list() == [3, 4]


# def test_selectors(nb1_0, selector, selector_kwargs):
#     assert False
# def test_get_item(nb1):
#     assert nb1['cells'] == nb1.nb['cells']
#
# def test_tag(self, tag_key, tag_value, selector, *args, **kwargs):
#     ...
#
# def to_ipynb(self, path):
#     write_ipynb(self.nb, path)

