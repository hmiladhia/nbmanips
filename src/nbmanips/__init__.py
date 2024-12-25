import nbmanips.exporters as _nb_exporters
from nbmanips.notebook import DBC, IPYNB, ZPLN, Notebook

__version__ = "2.1.2"
__author__ = "Dhia Hmila"
__all__ = ["DBC", "IPYNB", "ZPLN", "Notebook", "__version__", "__author__"]


# -- Register Exporters --
Notebook.register_exporter("dbc", _nb_exporters.DbcExporter, exporter_type="nbmanips")
