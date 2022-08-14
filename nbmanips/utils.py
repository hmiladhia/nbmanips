import json
import os
import urllib.parse
import warnings
import zipfile
from functools import wraps
from io import StringIO
from pathlib import Path
from typing import Tuple

import nbformat
from html2text import html2text

try:
    import pandas as pd
except ImportError:
    pd = None

# -- Constants --
# --- Attachment Constants ---
MD_IMG_REGEX = r'!\[(?P<ALT_TEXT>.*?)]\((?P<PATH>.*?)\)'
MD_IMG_EXPRESSION = r'![{ALT_TEXT}](attachment:{attachment_name})'
HTML_IMG_REGEX = (
    r'<img\s(?P<PREFIX>.*?)'
    r'src\s*=\s*\"?(?P<PATH>(?<=\")[^\"]*(?=\")|(?:[^\"\s]|(?<=\\)\s)*[^\s\\/])\"?'
    r'(?P<SUFFIX>.*?)>'
)
HTML_IMG_EXPRESSION = r'<img {PREFIX}src="attachment:{attachment_name}"{SUFFIX}>'

# --- READERS Constants ---
ZPLN_PREFIXES = {
    'python': {'%python', '%pyspark', '%spark.pyspark'},
}


def total_size(o):
    return len(json.dumps(o).encode('utf-8'))


def get_ipynb_name(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def read_ipynb(notebook_path: str, version=4) -> dict:
    nb_node = nbformat.read(notebook_path, as_version=version)
    raw_json = nbformat.writes(nb_node)
    return json.loads(raw_json)


def read_zpln(notebook_path: str, version=4, encoding='utf-8'):
    with open(notebook_path, 'r', encoding=encoding) as f:
        zep_nb = json.load(f)
    name = zep_nb.get('name', os.path.splitext(os.path.basename(notebook_path))[0])
    language = zep_nb.get('defaultInterpreterGroup', 'python')
    language_prefixes = ZPLN_PREFIXES.get(language, {'%' + language})
    notebook = {
        'metadata': {'language_info': {'name': language}},
        'nbformat': 4,
        'nbformat_minor': 4,
        'cells': [],
    }

    for paragraph in zep_nb.get('paragraphs', []):
        paragraph_config = paragraph.get('config', {})
        source_hidden = paragraph_config.get('editorHide', False)
        outputs_hidden = paragraph_config.get('tableHide', False)
        cell = {
            'metadata': {
                'collapsed': source_hidden and outputs_hidden,
                'jupyter': dict(
                    source_hidden=source_hidden, outputs_hidden=outputs_hidden
                ),
            }
        }
        title = paragraph.get('title', None)
        if title:
            cell['metadata']['name'] = title

        source = paragraph.get('text', '')
        prefix = source.split()[0].strip() if source.startswith('%') else None
        if prefix:
            suffix = '\n'.join(source.split('\n')[1:])
        else:
            suffix = source

        if prefix is not None and prefix.startswith('%md'):
            cell['source'] = suffix
            cell['cell_type'] = 'markdown'
            notebook['cells'].append(cell)
            continue

        if prefix is None or prefix in language_prefixes:
            cell['source'] = suffix
        else:
            cell['source'] = source

        cell['cell_type'] = 'code'
        cell['outputs'] = []
        if (
            paragraph.get('results', None)
            and paragraph['results'].get('code', None).upper() != 'ERROR'
        ):
            for result in paragraph['results'].get('msg', []):
                result_type = result.get('type', 'TEXT').upper()
                if result_type == 'TEXT':
                    data = result.get('data', '')
                    cell['outputs'].append(
                        {'output_type': 'stream', 'text': data, 'name': 'stdout'}
                    )
                elif result_type == 'TABLE':
                    data = result.get('data', '')
                    if pd is None:
                        cell['outputs'].append(
                            {'output_type': 'stream', 'text': data, 'name': 'stdout'}
                        )
                    else:
                        data = pd.read_csv(StringIO(data), sep='\t').to_html()
                        cell['outputs'].append(
                            {
                                'output_type': 'display_data',
                                'data': {'text/html': data},
                                'metadata': {},
                            }
                        )
                elif result_type in 'HTML':
                    data = result.get('data', '')
                    cell['outputs'].append(
                        {
                            'output_type': 'display_data',
                            'data': {'text/html': data},
                            'metadata': {},
                        }
                    )

        cell['execution_count'] = None

        notebook['cells'].append(cell)

    nb_node = nbformat.reads(json.dumps(notebook), as_version=version)
    raw_json = nbformat.writes(nb_node)
    return name, json.loads(raw_json)


def read_dbc(
    notebook_path: str, version=4, filename=None, encoding='utf-8'
) -> Tuple[str, dict]:

    if zipfile.is_zipfile(notebook_path):
        with zipfile.ZipFile(notebook_path, 'r') as zf:
            if filename is None:
                names = zf.namelist()
                files = [name for name in names if not name.endswith('/')]
                if len(files) > 1:
                    raise ValueError(
                        f'Multiple Notebooks in archive: {files}\nSpecify the notebook filename.'
                    )
                filename = files[0]

            dbc_nb = json.loads(zf.read(filename).decode(encoding))
    else:
        if filename is not None or filename != os.path.basename(notebook_path):
            raise ValueError(f'Invalid filename: {filename}')
        with open(notebook_path, 'r', encoding=encoding) as f:
            dbc_nb = json.load(f)

    name = dbc_nb.get('name', os.path.splitext(os.path.basename(notebook_path))[0])
    language = dbc_nb.get(
        'language', os.path.splitext(os.path.basename(notebook_path))[1]
    )
    language_prefix = f'%{language}' if language != 'python' else '%py'
    notebook = {
        'metadata': {'language_info': {'name': language}},
        'nbformat': 4,
        'nbformat_minor': 4,
        'cells': [],
    }

    for command in dbc_nb.get('commands', []):
        cell = {'metadata': {'collapsed': command.get('collapsed', False)}}
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
        if (
            command.get('results', None)
            and command['results'].get('type', None) == 'html'
        ):
            html = command['results'].get('data', '')
            cell['outputs'].append(
                {
                    'output_type': 'display_data',
                    'data': {'text/html': html},
                    'metadata': {},
                }
            )

        error_summary = html2text(command.get('errorSummary', None) or '')
        error = html2text(command.get('error', None) or '')
        if error_summary or error:
            if ':' in error_summary:
                ename, evalue = error_summary.split(':', 1)
            else:
                ename, evalue = '', error_summary
            cell['outputs'].append(
                {
                    'output_type': 'error',
                    'ename': ename,
                    'evalue': evalue,
                    'traceback': error.split('\n'),
                }
            )

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


def get_assets_path(nb, assets_path=None):
    if assets_path is None:
        assets_path = getattr(nb, '_original_path', None)
        if assets_path:
            return Path(assets_path).parent
        return Path.cwd()

    return Path(assets_path)


def burn_attachment(match, cell, assets_path: Path, expr):
    path = match.group('PATH')
    if path.startswith('attachment:'):
        return match.group(0)

    path = assets_path / urllib.parse.unquote(path)
    if not path.exists():
        path = match.group('PATH')
        warnings.warn(f"Couldn't find '{path}'")
        return match.group(0)

    match_dict = match.groupdict()
    attachment_name = match_dict.pop('PATH').replace(' ', '%20')
    cell.attach(str(path), attachment_name=attachment_name)
    return expr.format(**match_dict, attachment_name=attachment_name)
