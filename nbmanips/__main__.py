import colorama
import cloudpickle
import click

from nbmanips import Notebook
from nbmanips.selector import Selector
from nbmanips.cell_utils import styles

_COLORS = set(vars(colorama.Fore).keys()) - {'RESET'}


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
@click.option('--style', '-s', type=click.Choice(styles.keys()), default='single')
@click.option('--width', '-w', type=int, default=None)
@click.option('--color', '-c', type=click.Choice(_COLORS), default=None)
@click.option('--img-width', '-iw', type=int, default=None)
@click.option('--img-color', '-ic', type=click.Choice(_COLORS), default=None)
def show(notebook_path, width, style, color, img_color, img_width):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).show(width, style, color, img_color, img_width)


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


@nbmanips.command(help="replace string in all selected cells")
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option('--output-type', 'output_types', multiple=True)
def erase_output(notebook_path, output, output_types):
    output = notebook_path if output is None else output
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).erase_output(set(output_types))
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

    # import inspect
    # inspect.signature(function).parameters['b'].annotation

    sel = Selector(selector, *arguments, **dict(kwargs))
    piped_selector = get_selector()
    if piped_selector is not None:
        sel = Selector([piped_selector, sel])
    click.echo(cloudpickle.dumps(sel))


nbmanips.add_command(list_, 'list')


if __name__ == '__main__':
    nbmanips()
