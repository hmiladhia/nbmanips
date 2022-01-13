from pathlib import Path

import pytest
from click.testing import CliRunner

from nbmanips import IPYNB
from nbmanips.__main__ import nbmanips as cli


@pytest.fixture()
def runner():
    yield CliRunner()


def test_select_0(runner):
    selection_result = runner.invoke(cli, ['select', 'contains', 'df'])
    assert selection_result.exit_code == 0

    result = runner.invoke(cli, ['count', 'test_files/nb3.ipynb'], input=selection_result.stdout_bytes)

    assert result.exit_code == 0
    assert int(result.output.strip()) == 4


def test_select_1(runner):
    selection_result = runner.invoke(cli, ['select', 'has_output_type', 'text/plain'])
    assert selection_result.exit_code == 0

    result = runner.invoke(cli, ['count', 'test_files/nb1.ipynb'], input=selection_result.stdout_bytes)

    assert result.exit_code == 0
    assert result.output.strip() == '2'


def test_select_2(runner):
    import cloudpickle
    from nbmanips.selector import Selector

    selection_result = runner.invoke(cli, ['select', 'is_empty'])
    assert selection_result.exit_code == 0

    selector = cloudpickle.loads(selection_result.stdout_bytes)
    assert isinstance(selector, Selector)

    result = runner.invoke(cli, ['list', 'test_files/nb3.ipynb'], input=selection_result.stdout_bytes)

    assert result.exit_code == 0
    assert result.output.strip() == '[5, 8]'


@pytest.mark.parametrize('selection, expected_result', [('0', 1), ('1:3', 2)])
def test_select_3(runner, selection, expected_result):
    selection_result = runner.invoke(cli, ['select', selection])
    assert selection_result.exit_code == 0

    result = runner.invoke(cli, ['count', 'test_files/nb3.ipynb'], input=selection_result.stdout_bytes)

    assert result.exit_code == 0
    assert int(result.output.strip()) == expected_result


def test_to_html(runner):
    nb3 = Path('test_files/nb3.ipynb').read_text()
    with runner.isolated_filesystem():
        with open('nb.ipynb', 'w') as f:
            f.write(nb3)

        result = runner.invoke(cli, ['convert', 'html', 'nb.ipynb', '-o', 'exported.html'])
        assert result.exit_code == 0
        assert not Path('nb.html').exists()
        assert Path('exported.html').exists()


def test_to_slides(runner):
    nb3 = Path('test_files/nb3.ipynb').read_text()
    with runner.isolated_filesystem():
        with open('nb.ipynb', 'w') as f:
            f.write(nb3)

        result = runner.invoke(cli, ['convert', 'slides', 'nb.ipynb', '-o', 'exported.slides.html'])
        assert result.exit_code == 0
        assert Path('exported.slides.html').exists()


def test_to_py(runner):
    nb3 = Path('test_files/nb3.ipynb').read_text()
    with runner.isolated_filesystem():
        with open('nb.ipynb', 'w') as f:
            f.write(nb3)

        result = runner.invoke(cli, ['convert', 'py', 'nb.ipynb', '-o', 'exported.py'])
        assert result.exit_code == 0
        assert Path('exported.py').exists()


def test_to_md(runner):
    nb3 = Path('test_files/nb3.ipynb').read_text()
    with runner.isolated_filesystem():
        with open('nb.ipynb', 'w') as f:
            f.write(nb3)

        result = runner.invoke(cli, ['convert', 'md', 'nb.ipynb', '-o', 'exported.md'])
        assert result.exit_code == 0
        assert Path('exported.md').exists()


def test_show(runner):
    result = runner.invoke(cli, ['show', 'test_files/nb1.ipynb'])

    assert result.exit_code == 0
    assert len(result.output.strip().split('\n')) >= 3


def test_count(runner):
    result = runner.invoke(cli, ['count', 'test_files/nb1.ipynb'])

    assert result.exit_code == 0
    assert int(result.output.strip()) == 4


def test_first(runner):
    selection_result = runner.invoke(cli, ['select', 'is_empty'])
    assert selection_result.exit_code == 0

    result = runner.invoke(cli, ['first', 'test_files/nb3.ipynb'], input=selection_result.stdout_bytes)

    assert result.exit_code == 0
    assert int(result.output.strip()) == 5


def test_last(runner):
    selection_result = runner.invoke(cli, ['select', 'is_empty'])
    assert selection_result.exit_code == 0

    result = runner.invoke(cli, ['last', 'test_files/nb3.ipynb'], input=selection_result.stdout_bytes)

    assert result.exit_code == 0
    assert int(result.output.strip()) == 8


def test_list(runner):
    selection_result = runner.invoke(cli, ['select', 'is_empty'])
    assert selection_result.exit_code == 0

    result = runner.invoke(cli, ['list', 'test_files/nb3.ipynb'], input=selection_result.stdout_bytes)

    assert result.exit_code == 0
    assert result.output.strip() == '[5, 8]'


def test_search(runner):
    result = runner.invoke(cli, ['search', '-t', 'a', 'test_files/nb1.ipynb'])

    assert result.exit_code == 0
    assert result.output.strip() == '[0, 2, 3]'


def test_erase(runner):
    nb3 = Path('test_files/nb3.ipynb').read_text()
    with runner.isolated_filesystem():
        with open('nb.ipynb', 'w') as f:
            f.write(nb3)
        assert IPYNB('nb.ipynb').select('is_empty').count() == 2

        selection_result = runner.invoke(cli, ['select', '-i', 'is_empty'])
        assert selection_result.exit_code == 0

        result = runner.invoke(cli, ['erase', 'nb.ipynb'], input=selection_result.stdout_bytes)
        assert result.exit_code == 1

        result = runner.invoke(cli, ['erase', '-f', 'nb.ipynb'], input=selection_result.stdout_bytes)
        assert result.exit_code == 0

        assert IPYNB('nb.ipynb').select('is_empty').count() == 4

        result = runner.invoke(cli, ['erase', 'nb.ipynb', '-o', 'nb1.ipynb'], input=selection_result.stdout_bytes)
        assert result.exit_code == 0

        assert IPYNB('nb1.ipynb').select('is_empty').count() == 4


def test_delete(runner):
    nb3 = Path('test_files/nb3.ipynb').read_text()
    with runner.isolated_filesystem():
        with open('nb.ipynb', 'w') as f:
            f.write(nb3)
        assert IPYNB('nb.ipynb').count() == 9

        selection_result = runner.invoke(cli, ['select', 'is_empty'])
        assert selection_result.exit_code == 0

        result = runner.invoke(cli, ['delete', 'nb.ipynb'], input=selection_result.stdout_bytes)
        assert result.exit_code == 1

        result = runner.invoke(cli, ['delete', 'nb.ipynb', '-f'], input=selection_result.stdout_bytes)
        assert result.exit_code == 0

        nb = IPYNB('nb.ipynb')
        assert nb.select('is_empty').count() == 0
        assert nb.count() == 7

        result = runner.invoke(cli, ['delete', 'nb.ipynb', '-o', 'nb1.ipynb'], input=selection_result.stdout_bytes)
        assert result.exit_code == 0

        nb = IPYNB('nb1.ipynb')
        assert nb.select('is_empty').count() == 0
        assert nb.count() == 7


def test_keep(runner):
    nb3 = Path('test_files/nb3.ipynb').read_text()
    with runner.isolated_filesystem():
        with open('nb.ipynb', 'w') as f:
            f.write(nb3)
        assert IPYNB('nb.ipynb').count() == 9

        selection_result = runner.invoke(cli, ['select', 'is_empty'])
        assert selection_result.exit_code == 0

        result = runner.invoke(cli, ['keep', 'nb.ipynb'], input=selection_result.stdout_bytes)
        assert result.exit_code == 1

        result = runner.invoke(cli, ['keep', 'nb.ipynb', '-f'], input=selection_result.stdout_bytes)
        assert result.exit_code == 0

        nb = IPYNB('nb.ipynb')
        assert nb.count() == 2
        assert nb.select('is_empty').count() == 2

        result = runner.invoke(cli, ['keep', 'nb.ipynb', '-o', 'nb1.ipynb'], input=selection_result.stdout_bytes)
        assert result.exit_code == 0

        nb = IPYNB('nb1.ipynb')
        assert nb.count() == 2
        assert nb.select('is_empty').count() == 2


def test_replace(runner):
    nb3 = Path('test_files/nb3.ipynb').read_text()
    with runner.isolated_filesystem():
        with open('nb.ipynb', 'w') as f:
            f.write(nb3)
        assert len(IPYNB('nb.ipynb').search_all('df')) == 4

        result = runner.invoke(cli, ['replace', '-t', 'df', '-n', 'data', 'nb.ipynb'])
        assert result.exit_code == 1

        result = runner.invoke(cli, ['replace', '-t', 'df', '-n', 'data', '-f', 'nb.ipynb'])
        assert result.exit_code == 0

        nb = IPYNB('nb.ipynb')
        assert len(nb.search_all('df')) == 0
        assert len(nb.search_all('data')) == 4

        result = runner.invoke(cli, ['replace', '-t', 'df', '-n', 'data', 'nb.ipynb', '-o', 'nb1.ipynb'])
        assert result.exit_code == 0

        nb = IPYNB('nb1.ipynb')
        assert len(nb.search_all('df')) == 0
        assert len(nb.search_all('data')) == 4


def test_erase_output(runner):
    nb3 = Path('test_files/nb3.ipynb').read_text()
    with runner.isolated_filesystem():
        with open('nb.ipynb', 'w') as f:
            f.write(nb3)
        assert IPYNB('nb.ipynb').select('has_output').count() == 5

        result = runner.invoke(cli, ['erase-output', 'nb.ipynb'])
        assert result.exit_code == 1

        result = runner.invoke(cli, ['erase-output', 'nb.ipynb', '-f'])
        assert result.exit_code == 0

        assert IPYNB('nb.ipynb').select('has_output').count() == 0

        result = runner.invoke(cli, ['erase-output', 'nb.ipynb', '-o', 'nb1.ipynb'])
        assert result.exit_code == 0

        assert IPYNB('nb1.ipynb').select('has_output').count() == 0


def test_auto_slide(runner):
    nb3 = Path('test_files/nb3.ipynb').read_text()
    with runner.isolated_filesystem():
        with open('nb.ipynb', 'w') as f:
            f.write(nb3)

        nb = IPYNB('nb.ipynb')
        assert nb.select('has_slide_type', 'slide').count() == 0
        assert nb.select('has_slide_type', 'subslide').count() == 0

        result = runner.invoke(cli, ['auto-slide', 'nb.ipynb'])
        assert result.exit_code == 1

        result = runner.invoke(cli, ['auto-slide', 'nb.ipynb', '-f'])
        assert result.exit_code == 0

        nb = IPYNB('nb.ipynb')
        assert nb.select('has_slide_type', 'slide').count() == 0
        assert nb.select('has_slide_type', 'subslide').count() == 2

        result = runner.invoke(cli, ['auto-slide', 'nb.ipynb', '-o', 'nb1.ipynb'])
        assert result.exit_code == 0

        nb = IPYNB('nb1.ipynb')
        assert nb.select('has_slide_type', 'slide').count() == 0
        assert nb.select('has_slide_type', 'subslide').count() == 2
