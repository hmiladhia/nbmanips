import os
import pytest

from nbmanips import Notebook


@pytest.fixture(scope='session')
def output_files():
    # TODO: use temp folder
    import shutil
    directory = 'output_files'
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.mkdir(directory)
    yield directory
    shutil.rmtree(directory)


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
