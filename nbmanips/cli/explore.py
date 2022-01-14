import click
import colorama

from nbmanips import Notebook
from nbmanips.cell_utils import styles
from nbmanips.cli import get_selector

_COLORS = list(set(vars(colorama.Fore)) - {'RESET'})

__all__ = [
    'show',
    'count',
    'first',
    'last',
    'list_',
    'search'
]


@click.command(help="show notebook in human readable format")
@click.argument('notebook_path')
@click.option('--width', '-w', type=int, default=None)
@click.option('--output/--no-output', '-o/-no', type=bool, default=True)
@click.option('--exclude-output-type', '-e', 'excluded_data_types', multiple=True)
@click.option('--pygments/--no-pygments', '-p/-np', type=bool, default=None)
@click.option('--style', '-s', type=click.Choice(styles.keys(), case_sensitive=False), default='single')
@click.option('--border-color', '-bc', type=click.Choice(_COLORS, case_sensitive=False), default=None)
@click.option('--image-width', '-iw', type=int, default=None)
@click.option('--image-color/--no-image-color', '-ic/-nic', type=bool, default=None)
@click.option('--parser', '-p', 'parsers', type=str, multiple=True)
def show(notebook_path, width, pygments, output, style, border_color,
         parsers, image_width, image_color, excluded_data_types):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    parsers_config = None
    if image_width or image_color:
        parsers_config = {'image': {'width': image_width, 'colorful': image_color}}

    # image_color, image_width
    nb.select(selector).show(
        width,
        exclude_output=not output,
        use_pygments=pygments,
        style=style,
        border_color=border_color,
        parsers=parsers or None,
        parsers_config=parsers_config,
        excluded_data_types=excluded_data_types or None
    )


@click.command(help="count selected cells")
@click.argument('notebook_path')
def count(notebook_path):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    result = nb.select(selector).count()
    click.echo(result)


@click.command(help="Return the number of the first selected cell")
@click.argument('notebook_path')
def first(notebook_path):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    result = nb.select(selector).first()
    click.echo(result)


@click.command(help="Return the number of the last selected cell")
@click.argument('notebook_path')
def last(notebook_path):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    result = nb.select(selector).last()
    click.echo(result)


@click.command(help="Return the numbers of the selected cells")
@click.argument('notebook_path')
def list_(notebook_path):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    result = nb.select(selector).list()
    click.echo(result)


@click.command(help="Search string in all selected cells")
@click.argument('notebook_path')
@click.option('--text', '-t', required=True)
@click.option('--case/--no-case', default=False)
@click.option('--regex', '-r', is_flag=True, default=False)
@click.option('--output', '-o', is_flag=True, default=False)
def search(notebook_path, text, case, output, regex):
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    result = nb.select(selector).search_all(text, case, output, regex)
    click.echo(result)
