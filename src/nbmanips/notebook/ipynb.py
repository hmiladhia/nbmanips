from __future__ import annotations

from pathlib import Path

import nbformat

from nbmanips.notebook.notebook import Notebook, RawNotebookType


class IPYNB(Notebook):
    def __new__(cls, path: str, name: str | None = None) -> Notebook:
        return Notebook.read_ipynb(path, name)


def get_ipynb_name(path: str) -> str:
    return Path(path).stem


def get_nb_from_dict(
    nb_dict: RawNotebookType, as_version: int
) -> nbformat.NotebookNode:
    (major, minor) = nbformat.reader.get_version(nb_dict)
    nb = nbformat.versions[major].to_notebook_json(nb_dict, minor=minor)
    return nbformat.convert(nb, as_version)


def read_ipynb(notebook_path: str, version: int = 4) -> RawNotebookType:
    s = Path(notebook_path).read_text(encoding="utf-8")
    nb = nbformat.reader.reads(s)
    nb = nbformat.convert(nb, version)
    return dict(nb)


def write_ipynb(
    nb_dict: RawNotebookType, notebook_path: str, version: int | None = None
) -> None:
    nb_node = dict_to_ipynb(nb_dict)
    nbformat.write(
        nb_node, notebook_path, nbformat.NO_CONVERT if version is None else version
    )


def dict_to_ipynb(
    nb_dict: RawNotebookType, default_version: int = 4
) -> nbformat.NotebookNode:
    version = nb_dict.get("nbformat", default_version)
    return get_nb_from_dict(nb_dict, as_version=version)
