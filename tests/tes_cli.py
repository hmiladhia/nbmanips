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
