import os
import tempfile

import pytest

from nbmanips import Notebook


@pytest.fixture(scope='session')
def output_files():
    with tempfile.TemporaryDirectory() as directory:
        yield directory


@pytest.fixture(scope='session')
def nb1():
    return Notebook.read_ipynb('test_files/nb1.ipynb')


def test_to_ipynb(nb1, output_files):
    path = f'{output_files}/test.ipynb'
    nb1.to_ipynb(path)
    assert os.path.exists(path)


def test_to_text(nb1, output_files):
    path = f'{output_files}/test.txt'
    nb1.to_text(path)
    assert os.path.exists(path)


def test_to_html(nb1, output_files):
    path = f'{output_files}/test.html'
    nb1.to_html(path)
    assert os.path.exists(path)


def test_to_md(nb1, output_files):
    path = f'{output_files}/test.md'
    nb1.to_md(path)
    assert os.path.exists(path)


def test_to_slides(nb1, output_files):
    path = f'{output_files}/test.slides.html'
    nb1.to_slides(path)
    assert os.path.exists(path)


def test_to_py(nb1, output_files):
    path = f'{output_files}/test.py'
    nb1.to_py(path)
    assert os.path.exists(path)


def test_to_dbc(nb1, output_files):
    path = f'{output_files}/test_to.dbc'
    nb1.to_dbc(path)
    assert os.path.exists(path)
    assert isinstance(Notebook.read_dbc(path), Notebook)


@pytest.mark.parametrize('common_path', [None, 'test_files', '.'])
def test_dbc_exporter_multiple(nb1, output_files, common_path):
    from nbmanips.exporters import DbcExporter
    path = f'{output_files}/test_multiple.dbc'
    exp = DbcExporter()
    file_lists = [os.path.join('test_files', file) for file in os.listdir('test_files') if file.endswith('ipynb')]
    exp.write_dbc(file_lists, path, common_path)
    assert os.path.exists(path)


def test_dbc_exporter(nb1, output_files):
    from nbmanips.exporters import DbcExporter
    path = f'{output_files}/test.dbc'
    exp = DbcExporter()
    exp.export(nb1, path)
    assert os.path.exists(path)
