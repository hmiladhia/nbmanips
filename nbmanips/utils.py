import os
import json
from functools import wraps


def get_ipynb_name(path) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def read_ipynb(notebook_path, encoding='utf-8'):
    with open(notebook_path, 'r', encoding=encoding) as f:
        return json.load(f)


def write_ipynb(notebook, notebook_path, encoding='utf-8'):
    with open(notebook_path, 'w', encoding=encoding) as f:
        json.dump(notebook, f)


def partial(func, *args, **keywords):
    @wraps(func)
    def new_func(*f_args, **f_keywords):
        new_keywords = {**f_keywords, **keywords}
        return func(*f_args, *args, **new_keywords)
    return new_func
