import click

from nbmanips import Notebook
from nbmanips.cli import get_selector, export

__all__ = [
    'erase',
    'delete',
    'keep',
    'replace',
    'auto_slide',
    'erase_output'
]


@click.command(help="Erase the content of the selected cells")
@click.argument('notebook_path')
@click.option('--output', '-o', default=None, type=str)
@click.option(
    '--force', '-f', is_flag=True, default=False,
    help='Do not prompt for confirmation if file already exists'
)
def erase(notebook_path, output, force):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    nb.select(selector).erase()
    export(nb, notebook_path, output, force=force)


@click.command(help="Delete the selected cells")
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option(
    '--force', '-f', is_flag=True, default=False,
    help='Do not prompt for confirmation if file already exists'
)
def delete(notebook_path, output, force):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    nb.select(selector).delete()
    export(nb, notebook_path, output, force=force)


@click.command(help="Delete all the non-selected cells")
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option(
    '--force', '-f', is_flag=True, default=False,
    help='Do not prompt for confirmation if file already exists'
)
def keep(notebook_path, output, force):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    nb.select(selector).keep()
    export(nb, notebook_path, output, force=force)


@click.command(help="replace string in all selected cells")
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option('--old', '-t', required=True)
@click.option('--new', '-n', required=True)
@click.option('--count', '--max', '-m', 'count_', type=int, default=None)
@click.option('--regex', '-r', is_flag=True, default=False)
@click.option('--case/--no-case', '-c/-nc', default=True)
@click.option(
    '--force', '-f', is_flag=True, default=False,
    help='Do not prompt for confirmation if file already exists'
)
def replace(notebook_path, output, old, new, case, count_, regex, force):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    nb.select(selector).replace(old, new, count_, case, regex)
    export(nb, notebook_path, output, force=force)


@click.command(help="replace string in all selected cells")
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option('--max-cells', type=int, default=3)
@click.option('--max-images', type=int, default=1)
@click.option('--delete-empty/--keep-empty', 'delete_empty', default=True)
@click.option(
    '--force', '-f', is_flag=True, default=False,
    help='Do not prompt for confirmation if file already exists'
)
def auto_slide(notebook_path, output, max_cells, max_images, delete_empty, force):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    nb.select(selector).auto_slide(max_cells, max_images, delete_empty=delete_empty)
    export(nb, notebook_path, output, force=force)


@click.command(help="Erase the output content of the selected cells")
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option('--output-type', 'output_types', multiple=True)
@click.option(
    '--force', '-f', is_flag=True, default=False,
    help='Do not prompt for confirmation if file already exists'
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
