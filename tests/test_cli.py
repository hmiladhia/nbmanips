from pathlib import Path

import pytest
from click.testing import CliRunner

from nbmanips import IPYNB
from nbmanips.__main__ import nbmanips as cli


@pytest.fixture()
def runner():
    yield CliRunner()


def test_select_0(runner, test_files):
    selection_result = runner.invoke(cli, ['select', 'contains', 'df'])
    assert selection_result.exit_code == 0

    result = runner.invoke(
        cli,
        ['count', str(test_files / 'nb3.ipynb')],
        input=selection_result.stdout_bytes,
    )

    assert result.exit_code == 0
    assert int(result.output.strip()) == 4


def test_select_1(runner, test_files):
    selection_result = runner.invoke(cli, ['select', 'has_output_type', 'text/plain'])
    assert selection_result.exit_code == 0

    result = runner.invoke(
        cli,
        ['count', str(test_files / 'nb1.ipynb')],
        input=selection_result.stdout_bytes,
    )

    assert result.exit_code == 0
    assert result.output.strip() == '2'


def test_select_2(runner, test_files):
    import cloudpickle

    from nbmanips.selector import SelectorBase

    selection_result = runner.invoke(cli, ['select', 'is_empty'])
    assert selection_result.exit_code == 0

    selector = cloudpickle.loads(selection_result.stdout_bytes)
    assert isinstance(selector, SelectorBase)

    result = runner.invoke(
        cli,
        ['list', str(test_files / 'nb3.ipynb')],
        input=selection_result.stdout_bytes,
    )

    assert result.exit_code == 0
    assert result.output.strip() == '[5, 8]'


@pytest.mark.parametrize(
    'selection, expected_result',
    [
        ('0', 1),
        ('1:3', 2),
        ('[-3:]', 3),
        ('[-3]', 1),
        ('[1:-2]', 6),
    ],
)
def test_select_3(runner, test_files, selection, expected_result):
    selection_result = runner.invoke(cli, ['select', selection])
    assert selection_result.exit_code == 0

    result = runner.invoke(
        cli,
        ['count', str(test_files / 'nb3.ipynb')],
        input=selection_result.stdout_bytes,
    )

    assert result.exit_code == 0
    assert int(result.output.strip()) == expected_result


def test_to_html(runner, test_files):
    nb3 = Path(str(test_files / 'nb3.ipynb')).read_text()
    with runner.isolated_filesystem():
        Path('nb.ipynb').write_text(nb3)

        result = runner.invoke(
            cli, ['convert', 'html', 'nb.ipynb', '-o', 'exported.html']
        )
        assert result.exit_code == 0
        assert not Path('nb.html').exists()
        assert Path('exported.html').exists()


def test_to_slides(runner, test_files):
    nb3 = Path(str(test_files / 'nb3.ipynb')).read_text()
    with runner.isolated_filesystem():
        Path('nb.ipynb').write_text(nb3)

        result = runner.invoke(
            cli, ['convert', 'slides', 'nb.ipynb', '-o', 'exported.slides.html']
        )
        assert result.exit_code == 0
        assert Path('exported.slides.html').exists()


def test_to_py(runner, test_files):
    nb3 = Path(str(test_files / 'nb3.ipynb')).read_text()
    with runner.isolated_filesystem():
        Path('nb.ipynb').write_text(nb3)

        result = runner.invoke(cli, ['convert', 'py', 'nb.ipynb', '-o', 'exported.py'])
        assert result.exit_code == 0
        assert Path('exported.py').exists()


def test_to_md(runner, test_files):
    nb3 = Path(str(test_files / 'nb3.ipynb')).read_text()
    with runner.isolated_filesystem():
        Path('nb.ipynb').write_text(nb3)

        result = runner.invoke(cli, ['convert', 'md', 'nb.ipynb', '-o', 'exported.md'])
        assert result.exit_code == 0
        assert Path('exported.md').exists()


def test_show(runner, test_files):
    result = runner.invoke(cli, ['show', str(test_files / 'nb1.ipynb')])

    assert result.exit_code == 0
    assert len(result.output.strip().split('\n')) >= 3


def test_count(runner, test_files):
    result = runner.invoke(cli, ['count', str(test_files / 'nb1.ipynb')])

    assert result.exit_code == 0
    assert int(result.output.strip()) == 4


def test_first(runner, test_files):
    selection_result = runner.invoke(cli, ['select', 'is_empty'])
    assert selection_result.exit_code == 0

    result = runner.invoke(
        cli,
        ['first', str(test_files / 'nb3.ipynb')],
        input=selection_result.stdout_bytes,
    )

    assert result.exit_code == 0
    assert int(result.output.strip()) == 5


def test_last(runner, test_files):
    selection_result = runner.invoke(cli, ['select', 'is_empty'])
    assert selection_result.exit_code == 0

    result = runner.invoke(
        cli,
        ['last', str(test_files / 'nb3.ipynb')],
        input=selection_result.stdout_bytes,
    )

    assert result.exit_code == 0
    assert int(result.output.strip()) == 8


def test_list(runner, test_files):
    selection_result = runner.invoke(cli, ['select', 'is_empty'])
    assert selection_result.exit_code == 0

    result = runner.invoke(
        cli,
        ['list', str(test_files / 'nb3.ipynb')],
        input=selection_result.stdout_bytes,
    )

    assert result.exit_code == 0
    assert result.output.strip() == '[5, 8]'


def test_search(runner, test_files):
    result = runner.invoke(cli, ['search', '-t', 'a', str(test_files / 'nb1.ipynb')])

    assert result.exit_code == 0
    assert result.output.strip() == '[0, 2, 3]'


def test_erase(runner, test_files):
    nb3 = Path(str(test_files / 'nb3.ipynb')).read_text()
    with runner.isolated_filesystem():
        Path('nb.ipynb').write_text(nb3)
        assert IPYNB('nb.ipynb').select('is_empty').count() == 2

        selection_result = runner.invoke(cli, ['select', '-i', 'is_empty'])
        assert selection_result.exit_code == 0

        result = runner.invoke(
            cli, ['erase', 'nb.ipynb'], input=selection_result.stdout_bytes
        )
        assert result.exit_code == 1

        result = runner.invoke(
            cli, ['erase', '-f', 'nb.ipynb'], input=selection_result.stdout_bytes
        )
        assert result.exit_code == 0

        assert IPYNB('nb.ipynb').select('is_empty').count() == 4

        result = runner.invoke(
            cli,
            ['erase', 'nb.ipynb', '-o', 'nb1.ipynb'],
            input=selection_result.stdout_bytes,
        )
        assert result.exit_code == 0

        assert IPYNB('nb1.ipynb').select('is_empty').count() == 4


def test_delete(runner, test_files):
    nb3 = Path(str(test_files / 'nb3.ipynb')).read_text()
    with runner.isolated_filesystem():
        Path('nb.ipynb').write_text(nb3)
        assert IPYNB('nb.ipynb').count() == 9

        selection_result = runner.invoke(cli, ['select', 'is_empty'])
        assert selection_result.exit_code == 0

        result = runner.invoke(
            cli, ['delete', 'nb.ipynb'], input=selection_result.stdout_bytes
        )
        assert result.exit_code == 1

        result = runner.invoke(
            cli, ['delete', 'nb.ipynb', '-f'], input=selection_result.stdout_bytes
        )
        assert result.exit_code == 0

        nb = IPYNB('nb.ipynb')
        assert nb.select('is_empty').count() == 0
        assert nb.count() == 7

        result = runner.invoke(
            cli,
            ['delete', 'nb.ipynb', '-o', 'nb1.ipynb'],
            input=selection_result.stdout_bytes,
        )
        assert result.exit_code == 0

        nb = IPYNB('nb1.ipynb')
        assert nb.select('is_empty').count() == 0
        assert nb.count() == 7


def test_keep(runner, test_files):
    nb3 = Path(str(test_files / 'nb3.ipynb')).read_text()
    with runner.isolated_filesystem():
        Path('nb.ipynb').write_text(nb3)

        assert IPYNB('nb.ipynb').count() == 9

        selection_result = runner.invoke(cli, ['select', 'is_empty'])
        assert selection_result.exit_code == 0

        result = runner.invoke(
            cli, ['keep', 'nb.ipynb'], input=selection_result.stdout_bytes
        )
        assert result.exit_code == 1

        result = runner.invoke(
            cli, ['keep', 'nb.ipynb', '-f'], input=selection_result.stdout_bytes
        )
        assert result.exit_code == 0

        nb = IPYNB('nb.ipynb')
        assert nb.count() == 2
        assert nb.select('is_empty').count() == 2

        result = runner.invoke(
            cli,
            ['keep', 'nb.ipynb', '-o', 'nb1.ipynb'],
            input=selection_result.stdout_bytes,
        )
        assert result.exit_code == 0

        nb = IPYNB('nb1.ipynb')
        assert nb.count() == 2
        assert nb.select('is_empty').count() == 2


def test_replace(runner, test_files):
    nb3 = Path(str(test_files / 'nb3.ipynb')).read_text()
    with runner.isolated_filesystem():
        Path('nb.ipynb').write_text(nb3)

        assert len(IPYNB('nb.ipynb').search_all('df')) == 4

        result = runner.invoke(cli, ['replace', '-t', 'df', '-n', 'data', 'nb.ipynb'])
        assert result.exit_code == 1

        result = runner.invoke(
            cli, ['replace', '-t', 'df', '-n', 'data', '-f', 'nb.ipynb']
        )
        assert result.exit_code == 0

        nb = IPYNB('nb.ipynb')
        assert len(nb.search_all('df')) == 0
        assert len(nb.search_all('data')) == 4

        result = runner.invoke(
            cli, ['replace', '-t', 'df', '-n', 'data', 'nb.ipynb', '-o', 'nb1.ipynb']
        )
        assert result.exit_code == 0

        nb = IPYNB('nb1.ipynb')
        assert len(nb.search_all('df')) == 0
        assert len(nb.search_all('data')) == 4


def test_erase_output(runner, test_files):
    nb3 = Path(str(test_files / 'nb3.ipynb')).read_text()
    with runner.isolated_filesystem():
        Path('nb.ipynb').write_text(nb3)

        assert IPYNB('nb.ipynb').select('has_output').count() == 5

        result = runner.invoke(cli, ['erase-output', 'nb.ipynb'])
        assert result.exit_code == 1

        result = runner.invoke(cli, ['erase-output', 'nb.ipynb', '-f'])
        assert result.exit_code == 0

        assert IPYNB('nb.ipynb').select('has_output').count() == 0

        result = runner.invoke(cli, ['erase-output', 'nb.ipynb', '-o', 'nb1.ipynb'])
        assert result.exit_code == 0

        assert IPYNB('nb1.ipynb').select('has_output').count() == 0


def test_auto_slide(runner, test_files):
    nb3 = Path(str(test_files / 'nb3.ipynb')).read_text()
    with runner.isolated_filesystem():
        Path('nb.ipynb').write_text(nb3)

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


def test_split(runner, test_files):
    nb6 = Path(str(test_files / 'nb6.ipynb')).read_text()
    with runner.isolated_filesystem():
        Path('nb.ipynb').write_text(nb6)

        result = runner.invoke(cli, ['split', 'nb.ipynb', '1,6'])
        assert result.exit_code == 0

        for i in range(3):
            assert Path(f'nb-{i}.ipynb').exists()

        result = runner.invoke(
            cli, ['split', 'nb.ipynb', '-i', '1,9', '-o', 'new_nb-%d.ipynb']
        )
        assert result.exit_code == 0

        for i in range(3):
            assert Path(f'new_nb-{i}.ipynb').exists()

        result = runner.invoke(cli, ['split', 'nb.ipynb', '1,6'])
        assert result.exit_code == 1

        result = runner.invoke(cli, ['split', 'nb.ipynb', '1,6', '-f'])
        assert result.exit_code == 0


def test_split_on_selection(runner, test_files):
    nb6 = Path(str(test_files / 'nb6.ipynb')).read_text()
    with runner.isolated_filesystem():
        Path('nb.ipynb').write_text(nb6)

        selection_result = runner.invoke(cli, ['select', 'has_html_tag', 'h1'])
        assert selection_result.exit_code == 0

        selector = selection_result.stdout_bytes
        result = runner.invoke(cli, ['split', '-s', 'nb.ipynb', '1,6'], input=selector)
        assert result.exit_code == 1
        assert isinstance(result.exception, ValueError)

        selector = selection_result.stdout_bytes
        result = runner.invoke(cli, ['split', '-s', 'nb.ipynb'], input=selector)
        assert result.exit_code == 0

        for i in range(3):
            assert Path(f'nb-{i}.ipynb').exists() is True, f'nb-{i}.ipynb'


def test_toc(runner, test_files):
    nb6 = Path(str(test_files / 'nb6.ipynb')).read_text()
    with runner.isolated_filesystem():
        Path('nb.ipynb').write_text(nb6)

        result = runner.invoke(cli, ['toc', 'nb.ipynb', '-w', '60'])
        assert result.exit_code == 0
        assert len(result.output.strip().split('\n')) == 16


def test_cat(runner, test_files):
    nb1 = Path(str(test_files / 'nb1.ipynb')).read_text()
    nb2 = Path(str(test_files / 'nb2.ipynb')).read_text()
    with runner.isolated_filesystem():
        Path('nb1.ipynb').write_text(nb1)

        Path('nb2.ipynb').write_text(nb2)

        result = runner.invoke(
            cli, ['cat', 'nb1.ipynb', 'nb2.ipynb', '-o', 'nb3.ipynb']
        )
        assert result.exit_code == 0

        nb1 = IPYNB('nb1.ipynb')
        nb2 = IPYNB('nb2.ipynb')
        nb3 = IPYNB('nb3.ipynb')
        assert len(nb3) == len(nb1) + len(nb2)

        selector_result = runner.invoke(cli, ['select', '0'])
        result = runner.invoke(
            cli,
            ['cat', 'nb1.ipynb', 'nb2.ipynb', '-o', 'nb4.ipynb', '-s', '0'],
            input=selector_result.stdout_bytes,
        )
        assert result.exit_code == 0

        nb4 = IPYNB('nb4.ipynb')
        assert len(nb4) == 1 + len(nb2)

        result = runner.invoke(
            cli,
            ['cat', 'nb1.ipynb', 'nb2.ipynb', '-o', 'nb5.ipynb'],
            input=selector_result.stdout_bytes,
        )
        assert result.exit_code == 0

        nb5 = IPYNB('nb5.ipynb')
        assert len(nb5) == 2


def test_attachments(runner: CliRunner, test_files):
    import shutil

    nb7 = (test_files / 'nb7.ipynb').read_text()
    with runner.isolated_filesystem() as tmpdir:
        shutil.copytree(test_files / 'assets', Path(tmpdir) / 'assets')
        Path('nb.ipynb').write_text(nb7)

        original_size = len(nb7)

        result = runner.invoke(cli, ['burn', 'nb.ipynb', '-f'])
        assert result.exit_code == 0
        assert len(Path('nb.ipynb').read_text()) > 2 * original_size
