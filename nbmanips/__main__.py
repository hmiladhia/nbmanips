import cloudpickle

import click

from nbmanips import Notebook
from nbmanips.selector import Selector


def get_selector():
    if not click.get_text_stream('stdin').isatty():
        stream = click.get_binary_stream('stdin').read()
        selector = cloudpickle.loads(stream)
    else:
        selector = None
    return selector


@click.group()
def nbmanips():
    pass


@nbmanips.command(help="show notebook in human readable format")
@click.argument('notebook_path')
def show(notebook_path):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).show()


@nbmanips.command(help="count selected cells")
@click.argument('notebook_path')
def count(notebook_path):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    click.echo(nb.select(selector).count())


@nbmanips.command()
@click.argument('notebook_path')
def first(notebook_path):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    click.echo(nb.select(selector).first())


@nbmanips.command()
@click.argument('notebook_path')
def last(notebook_path):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    click.echo(nb.select(selector).last())


@click.command()
@click.argument('notebook_path')
def list_(notebook_path):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    click.echo(nb.select(selector).list())


@nbmanips.command(help="replace string in all selected cells")
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option('--old', required=True)
@click.option('--new', required=True)
@click.option('--count', type=int, default=None)
def replace(notebook_path, output, old, new, count):
    output = notebook_path if output is None else output
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).replace(old, new, count)
    nb.to_ipynb(output)


@nbmanips.command()
@click.argument('selector', required=True)
@click.argument('arguments', nargs=-1, required=False)
@click.option('--kwarg', 'kwargs', multiple=True, type=(str, str))
def select(selector, arguments, kwargs):
    if selector.isdigit():
        selector = int(selector)
    elif selector.replace(':', '').isdigit():
        selector = slice(*[int(p) for p in selector.split(':')])

    sel = Selector(selector, *arguments, **dict(kwargs))
    piped_selector = get_selector()
    if piped_selector is not None:
        sel = Selector([piped_selector, sel])
    click.echo(cloudpickle.dumps(sel))


nbmanips.add_command(list_, 'list')


if __name__ == '__main__':
    nbmanips()
