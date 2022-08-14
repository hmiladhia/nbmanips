import re

import nbformat
import pytest

from nbmanips import Notebook
from nbmanips.selector import Selector


def test_read_ipynb(nb1):
    assert len(nb1.raw_nb['cells']) == 4


def test_read(test_files):
    nb = Notebook.read(str(test_files / 'nb1.ipynb'))
    assert nb.count() == 4


def test_name(nb1):
    assert nb1.name == 'nb1'


def test_len_empty():
    assert (
        len(
            Notebook(
                {
                    'cells': [],
                    'nbformat': 4,
                    'nbformat_minor': 0,
                    'metadata': {},
                }
            )
        )
        == 0
    )


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


@pytest.mark.parametrize(
    'search_term,case,output,expected',
    [
        ('b', False, False, None),
        ('Hello', False, False, 1),
        ('hello', False, False, 1),
        ('hello', True, False, None),
        ('a', True, False, 0),
        ('a ', True, False, 2),
        ('125', True, False, None),
        ('125', True, True, 3),
    ],
)
def test_search(nb1, search_term, case, output, expected):
    assert nb1.search(search_term, case=case, output=output) == expected


@pytest.mark.parametrize(
    'search_term,case,output,expected',
    [
        ('b', False, False, None),
        (r'H\w+o', False, False, 1),
        (r'h\w+o', False, False, 1),
        (r'h\w+o', True, False, None),
        ('a', True, False, 0),
        ('a ', True, False, 2),
        ('125', True, False, None),
        ('125', True, True, 3),
    ],
)
def test_regex_search(nb1, search_term, case, output, expected):
    assert nb1.search(search_term, case=case, output=output, regex=True) == expected


@pytest.mark.parametrize(
    'search_term,case,output,expected',
    [
        ('b', False, False, []),
        ('Hello', False, False, [1]),
        ('hello', False, False, [1]),
        ('hello', True, False, []),
        ('a', True, False, [0, 2, 3]),
        ('a ', True, False, [2]),
        ('125', True, False, []),
        ('125', True, True, [3]),
    ],
)
def test_search_all(nb1, search_term, case, output, expected):
    assert nb1.search_all(search_term, case=case, output=output) == expected


@pytest.mark.parametrize(
    'old, new, case, count, regex, expected_old, expected_new',
    [
        ('jupyter', 'Test', True, None, False, [], []),
        ('Hello', 'Test', True, None, False, [], [1]),
        ('hello', 'Test', True, None, False, [], []),
        ('a', 'Test', True, None, False, [], [0, 2, 3]),
        ('a', 'Test', True, 1, False, [2, 3], [0]),
        ('a', 'Test', True, 2, False, [3], [0, 2]),
        ('A', 'Test', False, None, False, [], [0, 2, 3]),
        ('A', 'Test', True, None, False, [], []),
        (
            r'[A-Za-z_]\w*\s*=\s*\d+\s*[+-\/*]\s*\d+',
            'OPERATION',
            True,
            None,
            True,
            [],
            [2],
        ),
    ],
)
def test_replace(nb1_0, old, new, case, count, regex, expected_old, expected_new):
    nb1_0.replace(old, new, count=count, case=case, regex=regex)
    assert nb1_0.search_all(old, case=case) == expected_old
    assert nb1_0.search_all(new, case=True) == expected_new


@pytest.mark.parametrize(
    'selector, selector_kwargs, search_term, expected',
    [
        ('contains', {'text': 'Hello'}, 'World', []),
        ('contains', {'text': 'Hi'}, 'World', [1]),
        ('contains', {'text': 'a '}, 'a', [0, 3]),
    ],
)
def test_erase(nb1_0, selector, selector_kwargs, search_term, expected):
    nb1_0.select(selector, **selector_kwargs).erase()
    assert nb1_0.search_all(search_term, case=True) == expected
    assert len(nb1_0) == 4


def test_erase_output(nb3_0):
    assert nb3_0.select('has_output_type', 'image/png').count() == 2
    nb3_0.erase_output('image/png')
    assert nb3_0.select('has_output_type', 'image/png').count() == 0


@pytest.mark.parametrize(
    'selector, selector_kwargs, search_term, expected, expected_length',
    [
        ('contains', {'text': 'Hello'}, 'World', [], 3),
        ('contains', {'text': 'Hi'}, 'World', [1], 4),
        ('contains', {'text': 'a '}, 'a', [0, 2], 3),
    ],
)
def test_delete(
    nb1_0, selector, selector_kwargs, search_term, expected, expected_length
):
    nb1_0.select(selector, **selector_kwargs).delete()
    assert nb1_0.search_all(search_term, case=True) == expected
    assert len(nb1_0) == expected_length


@pytest.mark.parametrize(
    'selector, selector_kwargs, search_term, expected, expected_length',
    [
        ('contains', {'text': 'Hello'}, 'World', [0], 1),
        ('contains', {'text': 'Hi'}, 'World', [], 0),
        ('contains', {'text': 'a'}, 'a', [0, 1, 2], 3),
        ('contains', {'text': 'a '}, 'a', [0], 1),
    ],
)
def test_keep(nb1_0, selector, selector_kwargs, search_term, expected, expected_length):
    nb1_0.select(selector, **selector_kwargs).keep()
    assert nb1_0.search_all(search_term, case=True) == expected
    assert len(nb1_0) == expected_length


def test_tag(nb1_0):
    nb1_0.select(lambda cell: cell.num in {0, 1, 2}).update_cell_metadata(
        'test', {'key': 'value'}
    )
    nb1_0.select(lambda cell: cell.num == 1).update_cell_metadata(
        'test', {'key': 'new_value'}
    )
    assert nb1_0.cells[1]['metadata']['test']['key'] == 'new_value'
    assert nb1_0.cells[0]['metadata']['test']['key'] == 'value'


# @pytest.mark.parametrize("slice_", [(0, 3), (1, 3), (1, 1), (0,), (1, 3, 2)])
def test_get_item_selector(nb1):
    assert nb1[0:3].list() == list(range(0, 3))
    assert nb1[1:3].list() == list(range(1, 3))
    assert nb1[1:1].list() == list(range(1, 1))
    assert nb1[:0].list() == list(range(0))
    assert nb1[1:3:2].list() == list(range(1, 3, 2))
    assert nb1['has_output'].first() == 1
    assert nb1['contains', 'hello', False].first() == 1


@pytest.mark.parametrize(
    'selector,args,expected',
    [
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
    ],
)
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
    assert len(nb1) + 2 * len(nb5) == len(result_nb)


def test_apply(nb1_0):
    def replace(cell):
        if 'Hello' in cell.get_source():
            return None
        cell.set_source(cell.get_source().replace('a', 'b').split('\n'))
        return cell

    sel = Selector('contains', '=') | Selector('contains', 'H')
    nb1_0.select(sel).apply(replace)
    assert nb1_0.select('contains', 'b').list() == [1]
    assert nb1_0.select('contains', 'a').list() == [0, 2]
    assert nb1_0.select('contains', 'Hello').list() == []


def test_cover_auto_slide(nb6_0):
    nb6_0.auto_slide()
    assert nb6_0.select('has_slide_type', 'slide').list() == [0, 2, 4, 8, 12]
    assert nb6_0.select('has_slide_type', 'subslide').list() == [7, 11]


def test_cells_property(nb1):
    assert nb1.cells == nb1.raw_nb['cells']


def test_select_on_selection(nb6):
    result = nb6.select('is_markdown').split_on_selection()
    assert len(result) == 6
    assert sum(len(nb) for nb in result) == len(nb6)


@pytest.mark.parametrize(
    'value,expected',
    [
        ([], 1),
        ([0, 6], 2),
        ([1, 6], 3),
        ([1, 6, 9], 4),
        ([1, 6, 14], 4),
        ([1, 6, 15], 3),
        ([1, 6, 18], 3),
        ([1, 6, 18, 29], 3),
    ],
)
def test_select(nb6, value, expected):
    result = nb6.split(*value)
    assert len(result) == expected
    assert sum(len(nb) for nb in result) == len(nb6)


def test_toc(nb6):
    toc = nb6.ptoc(index=True)
    match = re.search(r'2\.1\sSubpart\s*\[\d+]', toc)

    assert match is not None

    max_width = max(len(line) for line in nb6.ptoc(width=40, index=True).split('\n'))

    assert max_width < 40


def test_add_toc(nb6_0):
    len_nb6 = len(nb6_0)
    nb6_0.add_toc(1, bullets=True)

    assert len(nb6_0) == len_nb6 + 1

    match = re.search(
        r'\[2\.1\sSubpart]\(#2\.1-Subpart\)', nb6_0[1].first_cell().source
    )

    assert match is not None

    assert nb6_0[1].select('has_html_tag', 'a').count() == 1


def test_and_operator(nb1):
    selection = nb1.select('contains', 'a') & nb1.select('contains', '=')
    assert selection.list() == [2]


def test_and_operator_error(nb1, nb2):
    with pytest.raises(ValueError):
        nb1.select('contains', 'a') & nb2.select('contains', '=')

    nb1.select('contains', 'a') & nb1.select('contains', '5').select('contains', '=')


def test_or_operator(nb1):
    selection = nb1.select('contains', 'o') | nb1.select('contains', '=')
    assert selection.list() == [1, 2]


def test_invert_operator(nb1):
    selection = ~nb1.select('contains', 'o')
    assert selection.list() == [0, 2, 3]


@pytest.mark.parametrize(
    'truncate,expected', [(None, 11), (4, 10), (8, 14), (15, 11), (11, 11), (-1, 11)]
)
def test_truncate(nb1, truncate, expected):
    result = nb1[1].to_str(truncate=truncate)
    output = '\n'.join(result.split('\n')[3:])

    assert len(output) == expected
    assert len(nb1[0].to_str(truncate=truncate)) == 16


@pytest.mark.parametrize('exclude_output,expected', [(False, 11), (True, 0)])
def test_exclude_output(nb1, exclude_output, expected):
    result = nb1[1].to_str(exclude_output=exclude_output)
    output = '\n'.join(result.split('\n')[3:])

    assert len(output) == expected
    assert len(nb1[0].to_str(exclude_output=exclude_output)) == 16


def test_attachments(nb7: Notebook):
    from pathlib import Path
    nb7.burn_attachments()
    
    expected_outputs = {
        5: '![python](attachment:assets/python.png)',
        6: '<img src="attachment:assets/python.png"/>',
        7: '<img src="attachment:assets/python.png"/>',
        8: '\n'.join([
            '![python](attachment:assets/python.png)',
            '',
            '<img src="attachment:assets/python.png"/>'
            ]),
        9: '\n'.join([
            '![python](attachment:assets/python%20logo.svg)',
            '![python](assets/python_logo.svg)' # Does Not Exist
        ]),
        10: '\n'.join([
            '![python](attachment:assets/python%20logo.svg)',
            '<img src="attachment:assets/python%20logo.svg" />',
            '<img src="attachment:assets/python%20logo.svg" />',
            '<img src="attachment:assets/python%20logo.svg" />',
        ])
           
    }
    for cell_idx, source in expected_outputs.items():
        cell = nb7.cells[cell_idx]
        assert cell['source'] == source
        assert len(cell['attachments']) == 1

    # Test idempotence
    nb7.burn_attachments()

    for cell_idx, source in expected_outputs.items():
        cell = nb7.cells[cell_idx]
        assert cell['source'] == source
        assert len(cell['attachments']) == 1
