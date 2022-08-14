from pathlib import Path

import nbmanips.exporters as _nb_exporters
from nbmanips.notebook import DBC, IPYNB, ZPLN, Notebook

__version__ = (Path(__file__).parent / 'VERSION').read_text(encoding='utf-8').strip()

__all__ = ['DBC', 'IPYNB', 'ZPLN', 'Notebook', '__version__']


# -- Register Exporters --
Notebook.register_exporter('dbc', _nb_exporters.DbcExporter, exporter_type='nbmanips')
