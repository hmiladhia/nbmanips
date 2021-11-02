import os
import json
from zipfile import ZipFile

from nbmanips import Notebook


class DbcExporter:
    @staticmethod
    def _to_dbc_notebook(nb: Notebook, name=None, language=None, version='NotebookV1') -> dict:
        if version != 'NotebookV1':
            raise ValueError(f'Unsupported version: {version}')

        # json part
        notebook = {'version': version, 'commands': []}

        # name
        if name is not None:
            notebook['name'] = name
        elif nb.name is not None:
            notebook['name'] = nb.name

        # language
        language = language or nb.language
        if language is not None:
            notebook['language'] = language

        for cell in nb.iter_cells():
            source = cell.source
            if cell.type == 'markdown':
                source = '%md\n' + source

            jupyter = cell.metadata.get('jupyter', {})

            command = {
                "version": "CommandV1",
                "commandTitle": cell.metadata.get('name', ''),
                "command": source,
                "collapsed": cell.metadata.get('collapsed', False),
                "hideCommandCode": jupyter.get('source_hidden', False),
                "hideCommandResult": jupyter.get('outputs_hidden', False),
            }
            notebook['commands'].append(command)

        return notebook

    def export(self, nb: Notebook, output_path: str, filename=None, **kwargs):
        dbc_nb = self._to_dbc_notebook(nb, **kwargs)
        filename = filename or f"{dbc_nb['name']}.{dbc_nb['language']}"
        with ZipFile(output_path, mode='w') as zf:
            zf.writestr(filename, json.dumps(dbc_nb))

    def _common_path(self, path: str):
        return os.path.abspath(os.path.join(path, os.pardir))

    def write_dbc(self, file_list, output_path, common_path=None):
        # absolute paths
        file_list = [os.path.abspath(file) for file in file_list]
        if common_path is None:
            common_path = os.path.commonpath([self._common_path(path) for path in file_list])
        else:
            common_path = os.path.abspath(common_path)
            if not os.path.isdir(common_path) or all(file.startswith(common_path) for file in file_list):
                raise ValueError(f'common_path: {common_path}')
        common_path_len = len(common_path) + 1

        with ZipFile(output_path, mode='w') as zf:
            for file_path in file_list:
                dbc_nb = self._to_dbc_notebook(Notebook.read_ipynb(file_path))
                default_filename = f"{dbc_nb['name']}.{dbc_nb.get('language', 'python')}"
                parent_path = self._common_path(file_path)[common_path_len:]
                zip_path = os.path.join(parent_path, default_filename)
                zf.writestr(zip_path, json.dumps(dbc_nb))
