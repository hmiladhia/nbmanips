import os
import json
import shutil
from textwrap import wrap


def get_ipynb_name(path):
    return os.path.splitext(os.path.basename(path))[0]


def read_ipynb(notebook_path):
    with open(notebook_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_ipynb(notebook, notebook_path):
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f)


def printable_cell(text, style='unicode'):
    width = shutil.get_terminal_size().columns - 1
    result_list = wrap(text, width-4)

    char = '║' if style == 'unicode' else '|'

    if style == 'unicode':
        result = '╔' + '═' * (width - 2) + '╗'
    else:
        result = '+' + '_' * (width-2) + '+'

    result += '\n'
    result += '\n'.join([f"{char} {line.ljust(width-4)} {char}" for line in result_list])
    result += '\n'
    if style == 'unicode':
        result += '╚' + '═' * (width - 2) + '╝'
    else:
        result += '+' + '_' * (width - 2) + '+'
    return result
