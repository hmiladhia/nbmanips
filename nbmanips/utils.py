import os
import json

from functools import wraps

import nbformat


def total_size(o):
    return len(json.dumps(o).encode('utf-8'))


def get_ipynb_name(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def read_ipynb(notebook_path: str, version=4) -> dict:
    nb_node = nbformat.read(notebook_path, as_version=version)
    raw_json = nbformat.writes(nb_node)
    return json.loads(raw_json)


def write_ipynb(nb_dict: dict, notebook_path: str, version=nbformat.NO_CONVERT) -> None:
    nb_node = dict_to_ipynb(nb_dict)
    nbformat.write(nb_node, notebook_path, version)


def dict_to_ipynb(nb_dict: dict, default_version=4) -> nbformat.NotebookNode:
    version = nb_dict.get('nbformat', default_version)
    return nbformat.reads(json.dumps(nb_dict), as_version=version)


def partial(func, *args, **keywords):
    @wraps(func)
    def new_func(*f_args, **f_keywords):
        new_keywords = {**f_keywords, **keywords}
        return func(*f_args, *args, **new_keywords)
    return new_func
