import colorama
import click

from nbmanips import Notebook, __version__
from nbmanips.cell_utils import styles
from nbmanips.cli.select import select, get_selector
from nbmanips.cli.convert import convert

_COLORS = list(set(vars(colorama.Fore)) - {'RESET'})


@click.group()
@click.version_option(__version__, prog_name='nbmanips')
def nbmanips():
    pass


@nbmanips.command(help="show notebook in human readable format")
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
    nb = Notebook.read_ipynb(notebook_path)
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


@nbmanips.command(help="count selected cells")
@click.argument('notebook_path')
def count(notebook_path):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    result = nb.select(selector).count()
    click.echo(result)


@nbmanips.command(help="Return the number of the first selected cell")
@click.argument('notebook_path')
def first(notebook_path):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    result = nb.select(selector).first()
    click.echo(result)


@nbmanips.command(help="Return the number of the last selected cell")
@click.argument('notebook_path')
def last(notebook_path):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    result = nb.select(selector).last()
    click.echo(result)


@click.command(help="Return the numbers of the selected cells")
@click.argument('notebook_path')
def list_(notebook_path):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    result = nb.select(selector).list()
    click.echo(result)


@nbmanips.command(help="Search string in all selected cells")
@click.argument('notebook_path')
@click.option('--text', '-t', required=True)
@click.option('--case/--no-case', default=False)
@click.option('--regex', '-r', is_flag=True, default=False)
@click.option('--output', '-o', is_flag=True, default=False)
def search(notebook_path, text, case, output, regex):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    result = nb.select(selector).search_all(text, case, output, regex)
    click.echo(result)


@nbmanips.command(help="Erase the content of the selected cells")
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
def erase(notebook_path, output):
    output = notebook_path if output is None else output
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).erase()
    nb.to_ipynb(output)


@nbmanips.command(help="Delete the selected cells")
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
def delete(notebook_path, output):
    output = notebook_path if output is None else output
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).delete()
    nb.to_ipynb(output)


@nbmanips.command(help="Delete all the non-selected cells")
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
def keep(notebook_path, output):
    output = notebook_path if output is None else output
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).keep()
    nb.to_ipynb(output)


@nbmanips.command(help="replace string in all selected cells")
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option('--old', required=True)
@click.option('--new', required=True)
@click.option('--count', 'count_', type=int, default=None)
@click.option('--regex', is_flag=True, default=False)
@click.option('--case/--no-case', default=True)
def replace(notebook_path, output, old, new, case, count_, regex):
    output = notebook_path if output is None else output
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).replace(old, new, count_, case, regex)
    nb.to_ipynb(output)


@nbmanips.command(help="replace string in all selected cells")
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option('--max-cells', type=int, default=3)
@click.option('--max-images', type=int, default=1)
@click.option('--delete-empty/--keep-empty', 'delete_empty', default=True)
def auto_slide(notebook_path, output, max_cells, max_images, delete_empty):
    output = notebook_path if output is None else output
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).auto_slide(max_cells, max_images, delete_empty=delete_empty)
    nb.to_ipynb(output)


@nbmanips.command(help="Erase the output content of the selected cells")
@click.argument('notebook_path')
@click.option('--output', '-o', default=None)
@click.option('--output-type', 'output_types', multiple=True)
def erase_output(notebook_path, output, output_types):
    output = notebook_path if output is None else output
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).erase_output(set(output_types))
    nb.to_ipynb(output)


nbmanips.add_command(convert)
nbmanips.add_command(select)
nbmanips.add_command(list_, 'list')


if __name__ == '__main__':
    nbmanips()
