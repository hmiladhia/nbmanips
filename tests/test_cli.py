from pathlib import Path

import pytest
from click.testing import CliRunner

from nbmanips.__main__ import nbmanips as cli


@pytest.fixture()
def runner():
    yield CliRunner()


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
