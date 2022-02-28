from functools import reduce
from operator import add

import click

from nbmanips import Notebook
from nbmanips.cli import export, get_selector

__all__ = [
    'cat',
]


@click.command(help='Concatenate Jupyter FILE(s) to standard output')
@click.argument('file', nargs=-1, required=True)
@click.option('--output', '-o', default=None)
@click.option(
    '--force',
    '-f',
    is_flag=True,
    default=False,
    help='Do not prompt for confirmation if file already exists',
)
@click.option(
    '--select',
    '-s',
    type=int,
    default=None,
    help='Notebook to apply selector on. if unused, selector will be applied to all notebooks',
)
def cat(file, select, output, force):
    nbs = [Notebook.read(notebook_path) for notebook_path in file]
    selector = get_selector()

    if select is None:
        nbs = [nb.select(selector) for nb in nbs]
    else:
        nbs[select] = nbs[select].select(selector)

    nb = reduce(add, nbs)
    if output:
        export(nb, ..., output, force=force)
    else:
        click.echo(nb.to_json())
