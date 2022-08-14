from pathlib import Path

import nbmanips.exporters
from nbmanips.notebook import DBC, IPYNB, ZPLN, Notebook


__version__ = (Path(__file__).parent / 'VERSION').read_text(encoding='utf-8').strip()

__all__ = ['DBC', 'IPYNB', 'ZPLN', 'Notebook', '__version__']
