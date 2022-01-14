# flake8: noqa
from nbmanips.notebook import Notebook
from nbmanips.notebook import IPYNB, DBC, ZPLN
import nbmanips.exporters

from os.path import dirname as _dir
from os.path import join as _join

with open(_join(_dir(__file__), 'VERSION'), "r", encoding="utf-8") as fh:
    __version__ = fh.read().strip()
