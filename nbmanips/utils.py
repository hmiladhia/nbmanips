import os
import json
import zipfile

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


def read_dbc(notebook_path: str, version=4, filename=None, encoding='utf-8') -> (str, dict):
    if zipfile.is_zipfile(notebook_path):
        with zipfile.ZipFile(notebook_path, 'r') as zf:
            if filename is None:
                names = zf.namelist()
                files = [name for name in names if not name.endswith('/') ]
                if len(files) > 1:
                    raise ValueError(f'Multiple Notebooks in archive: {files}\nSpecify the notebook filename.')
                filename = files[0]

            dbc_nb = json.loads(zf.read(filename).decode(encoding))
    else:
        if filename is not None or filename != os.path.basename(notebook_path):
            raise ValueError(f'Invalid filename: {filename}')
        with open(notebook_path, 'r', encoding=encoding) as f:
            dbc_nb = json.load(f)

    name = dbc_nb.get('name', os.path.splitext(os.path.basename(notebook_path))[0])
    language = dbc_nb.get('language', os.path.splitext(os.path.basename(notebook_path))[1])
    language_prefix = f'%{language}' if language != 'python' else '%py'
    notebook = {
        "metadata": {
            "language_info": {
                "name": language
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4,
        "cells": []
    }

    for command in dbc_nb.get('commands', []):
        cell = {
            'metadata': {
                'collapsed': command.get('collapsed', False)
            }
        }
        source = command.get('command', '')
        prefix = source.split('\n')[0].strip() if source.startswith('%') else None
        if prefix:
            suffix = '\n'.join(source.split('\n')[1:])
        else:
            suffix = source

        if prefix is not None and prefix.startswith('%md'):
            cell['source'] = suffix
            cell['cell_type'] = 'markdown'
            notebook['cells'].append(cell)
            continue

        if prefix is None or prefix == language_prefix:
            cell['source'] = suffix
        else:
            cell['source'] = source

        cell['cell_type'] = 'code'
        cell['outputs'] = []
        cell['execution_count'] = None

        notebook['cells'].append(cell)

    nb_node = nbformat.reads(json.dumps(notebook), as_version=version)
    raw_json = nbformat.writes(nb_node)
    return name, json.loads(raw_json)


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
