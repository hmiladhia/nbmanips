import json
import os
import zipfile

from nbmanips.notebook import Notebook


def _parent_directory(path: str):
    return os.path.abspath(os.path.join(path, os.pardir))


def _get_dirs(path, common_path):
    dirs = set()
    while path.startswith(common_path):
        rel_path = os.path.relpath(path, common_path)
        if rel_path in dirs:
            break
        dirs.add(rel_path)
        path = _parent_directory(path)
    return dirs


class DbcExporter:
    @staticmethod
    def _to_dbc_notebook(
        nb: Notebook, name=None, language=None, version='NotebookV1'
    ) -> dict:
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

            results = [
                output.to_html()
                for output in cell.outputs
                if output.output_type != 'error'
            ]
            errors = [
                output for output in cell.outputs if output.output_type == 'error'
            ]

            command = {
                'version': 'CommandV1',
                'commandTitle': cell.metadata.get('name', ''),
                'command': source,
                'results': None,
                'errorSummary': None,
                'error': None,
                'collapsed': cell.metadata.get('collapsed', False),
                'hideCommandCode': jupyter.get('source_hidden', False),
                'hideCommandResult': jupyter.get('outputs_hidden', False),
            }

            if results:
                content = '\n'.join(results)
                command['results'] = {
                    'type': 'html',
                    'data': f"<div class=\"ansiout\">{content}</div>",
                }

            if errors:
                error = errors[0]
                command[
                    'errorSummary'
                ] = f"<span class=\"ansired\">{error.ename}</span>: {error.evalue}"
                command[
                    'error'
                ] = f"<div class=\"ansiout\">{error.to_html()}\n{command['errorSummary']}</div>"

            notebook['commands'].append(command)

        return notebook

    def export(self, nb: Notebook, output_path: str, filename=None, **kwargs):
        dbc_nb = self._to_dbc_notebook(nb, **kwargs)
        filename = filename or f"{dbc_nb['name']}.{dbc_nb['language']}"
        with zipfile.ZipFile(output_path, mode='w') as zf:
            zf.writestr(filename, json.dumps(dbc_nb))

    @staticmethod
    def _check_common_path(file_list, common_path):
        if common_path is None:
            common_path = os.path.commonpath(
                [_parent_directory(path) for path in file_list]
            )
        else:
            common_path = os.path.abspath(common_path)
            if not os.path.isdir(common_path):
                raise ValueError(f'common_path ({common_path}) is not a directory')
            invalid = list(
                filter(lambda file: not file.startswith(common_path), file_list)
            )
            if invalid:
                raise ValueError(
                    f'files: {invalid} should start with common_path: {common_path}'
                )
        return common_path

    def write_dbc(self, file_list, output_path, common_path=None):
        # absolute paths
        file_list = [os.path.abspath(file) for file in file_list]
        common_path = self._check_common_path(file_list, common_path)

        dirs = set()
        with zipfile.ZipFile(output_path, mode='w') as zf:
            for file_path in file_list:
                dbc_nb = self._to_dbc_notebook(Notebook.read_ipynb(file_path))
                default_filename = (
                    f"{dbc_nb['name']}.{dbc_nb.get('language', 'python')}"
                )
                parent_path = _parent_directory(file_path)
                dirs |= _get_dirs(parent_path, common_path)
                zip_path = os.path.join(
                    os.path.relpath(parent_path, common_path), default_filename
                )
                zf.writestr(zip_path, json.dumps(dbc_nb))

            for directory in dirs:
                zip_info = zipfile.ZipInfo(directory + '/')
                content = {
                    'version': 'FolderV1',
                    'name': directory,
                    'guid': '',
                    'children': [],
                }
                zf.writestr(zip_info, json.dumps(content))
