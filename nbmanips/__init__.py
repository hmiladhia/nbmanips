# flake8: noqa
from os.path import dirname as _dir
from os.path import join as _join

import nbmanips.exporters
from nbmanips.notebook import DBC, IPYNB, ZPLN, Notebook

with open(_join(_dir(__file__), 'VERSION'), 'r', encoding='utf-8') as fh:
    __version__ = fh.read().strip()
