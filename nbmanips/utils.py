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


styles = {"single": "││┌─┐└─┘",
          "double": "║║╔═╗╚═╝",
          "grid": '||+-++-+',
          "separated": '||+=++=+',
          "rounded": "||.-.'-'",
          "dots": "::......",
          "simple": '  ======',
          }


def parse_style(style):
    l, r, ul, u, ur, dl, d, dr = style

    return l, r, ul, u, ur, dl, d, dr


def printable_cell(text, width=None, style='single'):
    width = width or (shutil.get_terminal_size().columns - 1)
    style_l, style_r, style_ul, style_u, style_ur, style_dl, style_d, style_dr = parse_style(styles[style])

    text_width = width - 2 - len(style_l) - len(style_r)

    result_list = []
    for text_line in text.split('\n'):
        result_list.extend(wrap(text_line, text_width, tabsize=4))

    result = [style_ul + style_u * (width - len(style_ul) - len(style_ur)) + style_ur]
    result.extend([f"{style_l} {line.ljust(text_width)} {style_r}" for line in result_list])
    result.append(style_dl + style_d * (width - len(style_dl) - len(style_dr)) + style_dr)
    return '\n'.join(result)
