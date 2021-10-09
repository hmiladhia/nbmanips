import os
import colorama
import cloudpickle
import click

from nbmanips import Notebook, __version__
from nbmanips.selector import Selector
from nbmanips.cell_utils import styles

_COLORS = list(set(vars(colorama.Fore).keys()) - {'RESET'})


def get_selector():
    if not click.get_text_stream('stdin').isatty():
        stream = click.get_binary_stream('stdin').read()
        selector = cloudpickle.loads(stream)
    else:
        selector = None
    return selector


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

    click.echo(nb.select(selector).count())


@nbmanips.command(help="Return the number of the first selected cell")
@click.argument('notebook_path')
def first(notebook_path):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    click.echo(nb.select(selector).first())


@nbmanips.command(help="Return the number of the last selected cell")
@click.argument('notebook_path')
def last(notebook_path):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    click.echo(nb.select(selector).last())


@click.command(help="Return the numbers of the selected cells")
@click.argument('notebook_path')
def list_(notebook_path):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    click.echo(nb.select(selector).list())


@nbmanips.command(help="Search string in all selected cells")
@click.argument('notebook_path')
@click.option('--text', '-t', required=True)
@click.option('--case/--no-case', default=False)
@click.option('--regex', '-r', is_flag=True, default=False)
@click.option('--output', '-o', is_flag=True, default=False)
def search(notebook_path, text, case, output, regex):
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).search_all(text, case, output, regex)


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


@nbmanips.group(help="Convert a notebook to another format")
def convert():
    pass


@convert.command(help="Exports a basic HTML document.")
@click.argument('notebook_path')
@click.option('--output', '-o', help="path to export to", default=None)
@click.option('--template-name', '-t', help="the name of the template to use", default=None)
@click.option('--exclude-code-cell', is_flag=True, help="exclude code cells from all templates", default=False)
@click.option('--exclude-markdown', is_flag=True, help="exclude markdown cells from all templates", default=False)
@click.option('--exclude-raw', is_flag=True, help="exclude unknown cells from all templates", default=False)
@click.option('--exclude-unknown', is_flag=True, help="exclude unknown cells from all templates", default=False)
@click.option('--exclude-input', is_flag=True, help="exclude input prompts from all templates", default=False)
@click.option('--exclude-output', is_flag=True, help="exclude output prompts from all templates", default=False)
@click.option('--kwarg', 'kwargs', multiple=True, help="any additional parameters", type=(str, str))
def html(
        notebook_path,
        output,
        template_name,
        exclude_code_cell,
        exclude_markdown,
        exclude_raw,
        exclude_unknown,
        exclude_input,
        exclude_output,
        kwargs
):
    if output is None:
        output = os.path.splitext(notebook_path)[0] + '.html'
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).to_html(
        output,
        template_name=template_name,
        exclude_code_cell=exclude_code_cell,
        exclude_markdown=exclude_markdown,
        exclude_raw=exclude_raw,
        exclude_unknown=exclude_unknown,
        exclude_input=exclude_input,
        exclude_output=exclude_output,
        **dict(kwargs)
    )


@convert.command(help="Exports to a markdown document (.md)")
@click.argument('notebook_path')
@click.option('--output', '-o', help="path to export to", default=None)
@click.option('--template-name', '-t', help="the name of the template to use", default=None)
@click.option('--exclude-code-cell', is_flag=True, help="exclude code cells from all templates", default=False)
@click.option('--exclude-markdown', is_flag=True, help="exclude markdown cells from all templates", default=False)
@click.option('--exclude-raw', is_flag=True, help="exclude unknown cells from all templates", default=False)
@click.option('--exclude-unknown', is_flag=True, help="exclude unknown cells from all templates", default=False)
@click.option('--exclude-input', is_flag=True, help="exclude input prompts from all templates", default=False)
@click.option('--exclude-output', is_flag=True, help="exclude output prompts from all templates", default=False)
@click.option('--kwarg', 'kwargs', multiple=True, help="any additional parameters", type=(str, str))
def md(
        notebook_path,
        output,
        template_name,
        exclude_code_cell,
        exclude_markdown,
        exclude_raw,
        exclude_unknown,
        exclude_input,
        exclude_output,
        kwargs
):
    if output is None:
        output = os.path.splitext(notebook_path)[0] + '.md'
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).to_md(
        output,
        template_name=template_name,
        exclude_code_cell=exclude_code_cell,
        exclude_markdown=exclude_markdown,
        exclude_raw=exclude_raw,
        exclude_unknown=exclude_unknown,
        exclude_input=exclude_input,
        exclude_output=exclude_output,
        **dict(kwargs)
    )


@convert.command(help="Exports a Python code file.")
@click.argument('notebook_path')
@click.option('--output', '-o', help="path to export to", default=None)
@click.option('--template-name', '-t', help="the name of the template to use", default=None)
@click.option('--kwarg', 'kwargs', multiple=True, help="any additional parameters", type=(str, str))
def py(notebook_path, output, template_name, kwargs):
    if output is None:
        output = os.path.splitext(notebook_path)[0] + '.py'
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).to_py(output, template_name=template_name, **dict(kwargs))


@convert.command(help="Exports HTML slides with reveal.js")
@click.argument('notebook_path')
@click.option('--output', '-o', help="path to export to", default=None)
@click.option('--template-name', '-t', help="the name of the template to use", default=None)
@click.option('--exclude-code-cell', is_flag=True, help="exclude code cells from all templates", default=False)
@click.option('--exclude-markdown', is_flag=True, help="exclude markdown cells from all templates", default=False)
@click.option('--exclude-raw', is_flag=True, help="exclude unknown cells from all templates", default=False)
@click.option('--exclude-unknown', is_flag=True, help="exclude unknown cells from all templates", default=False)
@click.option('--exclude-input', is_flag=True, help="exclude input prompts from all templates", default=False)
@click.option('--exclude-output', is_flag=True, help="exclude output prompts from all templates", default=False)
@click.option('--theme', help="Name of the reveal.js theme to use.", default='simple')
@click.option('--transition', help="Name of the reveal.js transition to use", default='slide')
@click.option('--scroll/--no-scroll', type=bool, help="enable scrolling within each slide", default=True)
@click.option('--kwarg', 'kwargs', multiple=True, help="any additional parameters", type=(str, str))
def slides(
        notebook_path,
        output,
        template_name,
        exclude_code_cell,
        exclude_markdown,
        exclude_raw,
        exclude_unknown,
        exclude_input,
        exclude_output,
        scroll,
        transition,
        theme,
        kwargs
):
    if output is None:
        output = os.path.splitext(notebook_path)[0] + '.slides.html'
    nb = Notebook.read_ipynb(notebook_path)
    selector = get_selector()

    nb.select(selector).to_slides(
        output,
        template_name=template_name,
        exclude_code_cell=exclude_code_cell,
        exclude_markdown=exclude_markdown,
        exclude_raw=exclude_raw,
        exclude_unknown=exclude_unknown,
        exclude_input=exclude_input,
        exclude_output=exclude_output,
        scroll=scroll,
        transition=transition,
        theme=theme,
        **dict(kwargs)
    )


@nbmanips.command()
@click.argument('selector', required=True)
@click.argument('arguments', nargs=-1, required=False)
@click.option('--kwarg', 'kwargs', multiple=True, type=(str, str))
@click.option('--or', 'or_', is_flag=True, default=False)
@click.option('--invert', '-i', is_flag=True, default=False)
def select(selector, arguments, kwargs, or_, invert):
    if selector.isdigit():
        selector = int(selector)
    elif selector.replace(':', '').isdigit():
        selector = slice(*[int(p) for p in selector.split(':')])

    sel = Selector(selector, *arguments, **dict(kwargs))
    if invert:
        sel = ~sel

    piped_selector = get_selector()
    if piped_selector is not None:
        sel = (piped_selector | sel) if or_ else (piped_selector & sel)

    click.echo(cloudpickle.dumps(sel))


nbmanips.add_command(list_, 'list')


if __name__ == '__main__':
    nbmanips()
