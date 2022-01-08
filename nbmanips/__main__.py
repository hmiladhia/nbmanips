import click

from nbmanips import Notebook, __version__
from nbmanips.cli.select import select, get_selector
from nbmanips.cli.convert import convert
import nbmanips.cli.explore as explore


@click.group()
@click.version_option(__version__, prog_name='nbmanips')
def nbmanips():
    pass


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

for command in explore.__all__:
    nbmanips.add_command(getattr(explore, command), command.strip('_'))


if __name__ == '__main__':
    nbmanips()
