import os.path
from functools import reduce
from operator import add

import click

from nbmanips import Notebook
from nbmanips.cli import export, get_selector

__all__ = [
    'erase',
    'delete',
    'keep',
    'replace',
    'auto_slide',
    'erase_output',
    'split',
    'burn',
]


@click.command(help='Erase the content of the selected cells')
@click.argument('notebook_path')
@click.option('--output', '-o', default=None, type=str)
@click.option(
    '--force',
    '-f',
    is_flag=True,
    default=False,
    help='Do not prompt for confirmation if file already exists',
)
def erase(notebook_path, output, force):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    nb.select(selector).erase()
    export(nb, notebook_path, output, force=force)


@click.command(help='Delete the selected cells')
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option(
    '--force',
    '-f',
    is_flag=True,
    default=False,
    help='Do not prompt for confirmation if file already exists',
)
def delete(notebook_path, output, force):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    nb.select(selector).delete()
    export(nb, notebook_path, output, force=force)


@click.command(help='Delete all the non-selected cells')
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option(
    '--force',
    '-f',
    is_flag=True,
    default=False,
    help='Do not prompt for confirmation if file already exists',
)
def keep(notebook_path, output, force):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    nb.select(selector).keep()
    export(nb, notebook_path, output, force=force)


@click.command(help='replace string in all selected cells')
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option('--old', '-t', required=True)
@click.option('--new', '-n', required=True)
@click.option('--count', '--max', '-m', 'count_', type=int, default=None)
@click.option('--regex', '-r', is_flag=True, default=False)
@click.option('--case/--no-case', '-c/-nc', default=True)
@click.option(
    '--force',
    '-f',
    is_flag=True,
    default=False,
    help='Do not prompt for confirmation if file already exists',
)
def replace(notebook_path, output, old, new, case, count_, regex, force):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    nb.select(selector).replace(old, new, count_, case, regex)
    export(nb, notebook_path, output, force=force)


@click.command(help='replace string in all selected cells')
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option('--max-cells', type=int, default=3)
@click.option('--max-images', type=int, default=1)
@click.option('--delete-empty/--keep-empty', 'delete_empty', default=True)
@click.option(
    '--force',
    '-f',
    is_flag=True,
    default=False,
    help='Do not prompt for confirmation if file already exists',
)
def auto_slide(notebook_path, output, max_cells, max_images, delete_empty, force):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    nb.select(selector).auto_slide(max_cells, max_images, delete_empty=delete_empty)
    export(nb, notebook_path, output, force=force)


@click.command(help='Erase the output content of the selected cells')
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option('--output-type', 'output_types', multiple=True)
@click.option(
    '--force',
    '-f',
    is_flag=True,
    default=False,
    help='Do not prompt for confirmation if file already exists',
)
def erase_output(notebook_path, output, output_types, force):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    if output_types:
        output_types = set(output_types)
    else:
        output_types = None

    nb.select(selector).erase_output(output_types)
    export(nb, notebook_path, output, force=force)


@click.command(help='Split the notebook based the cell indexes')
@click.argument('notebook_path')
@click.argument('indexes', nargs=-1, required=False)
@click.option('--output', '-o', default=None)
@click.option('--index', '-i', multiple=True)
@click.option('--use-selection', '-s', is_flag=True, default=False)
@click.option(
    '--force',
    '-f',
    is_flag=True,
    default=False,
    help='Do not prompt for confirmation if file already exists',
)
def split(notebook_path, output, indexes, index, force, use_selection):
    if index or indexes:
        indexes = reduce(
            add, [index.split(',') for index in list(indexes) + list(index)]
        )
        indexes = [int(index) for index in indexes]
    elif not use_selection:
        raise ValueError('You need to specify the cells to split on')

    if indexes and use_selection:
        raise ValueError('Cannot use selection and indexes at the same time')

    nb = Notebook.read(notebook_path)
    selector = get_selector()

    if use_selection:
        nbs = nb.select(selector).split_on_selection()
    else:
        nbs = nb.select(selector).split(*indexes)

    # Exporting
    base, ext = os.path.splitext(notebook_path)
    input_path = base + '-%d' + ext
    for i, nb in enumerate(nbs):
        if output:
            output_path = output % i
        else:
            output_path = None
        export(nb, input_path % i, output_path, force=force)


@click.command(help='Burn the images in markdown cells as attachments')
@click.argument('notebook_path')
@click.option(
    '--assets-path',
    '-a',
    type=str,
    default=None,
    help='Path of the assets used in the notebook',
)
@click.option(
    '--html/--no-html',
    is_flag=True,
    default=True,
    help='burn images in img html tags as attachments',
)
@click.option('--output', '-o', default=None)
@click.option(
    '--force',
    '-f',
    is_flag=True,
    default=False,
    help='Do not prompt for confirmation if file already exists',
)
def burn(notebook_path, assets_path, output, force, html):
    nb: Notebook = Notebook.read(notebook_path)
    selector = get_selector()

    nb.select(selector).burn_attachments(assets_path=assets_path, html=html)
    export(nb, notebook_path, output, force=force)
