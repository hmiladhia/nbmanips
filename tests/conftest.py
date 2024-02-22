from pathlib import Path

import pytest

from nbmanips import Notebook


@pytest.fixture(scope="session")
def test_files() -> Path:
    return Path(__file__).parent / "test_files"


@pytest.fixture()
def nb1_0(test_files: Path) -> Notebook:
    return Notebook.read_ipynb(test_files / "nb1.ipynb")


@pytest.fixture()
def nb3_0(test_files: Path) -> Notebook:
    return Notebook.read_ipynb(test_files / "nb3.ipynb")


@pytest.fixture()
def nb6_0(test_files: Path) -> Notebook:
    return Notebook.read_ipynb(test_files / "nb6.ipynb")


@pytest.fixture(scope="session")
def nb1(test_files: Path) -> Notebook:
    return Notebook.read_ipynb(test_files / "nb1.ipynb")


@pytest.fixture(scope="session")
def nb2(test_files: Path) -> Notebook:
    return Notebook.read_ipynb(test_files / "nb2.ipynb")


@pytest.fixture(scope="session")
def nb3(test_files: Path) -> Notebook:
    """Notebook with images."""
    return Notebook.read_ipynb(test_files / "nb3.ipynb")


@pytest.fixture(scope="session")
def nb5(test_files: Path) -> Notebook:
    """Notebook in version 4.5."""
    return Notebook.read_ipynb(test_files / "nb5.ipynb")


@pytest.fixture(scope="session")
def nb6(test_files: Path) -> Notebook:
    return Notebook.read_ipynb(test_files / "nb6.ipynb")


@pytest.fixture()
def nb7(test_files: Path) -> Notebook:
    return Notebook.read_ipynb(test_files / "nb7.ipynb")
