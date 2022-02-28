import os

import click

from nbmanips import Notebook
from nbmanips.cli import get_selector

__all__ = ['convert']


@click.group(help='Convert a notebook to another format')
def convert():
    pass


@convert.command(help='Exports a basic HTML document.')
@click.argument('notebook_path')
@click.option('--output', '-o', help='path to export to', default=None)
@click.option(
    '--template-name', '-t', help='the name of the template to use', default=None
)
@click.option(
    '--exclude-code-cell',
    is_flag=True,
    help='exclude code cells from all templates',
    default=False,
)
@click.option(
    '--exclude-markdown',
    is_flag=True,
    help='exclude markdown cells from all templates',
    default=False,
)
@click.option(
    '--exclude-raw',
    is_flag=True,
    help='exclude unknown cells from all templates',
    default=False,
)
@click.option(
    '--exclude-unknown',
    is_flag=True,
    help='exclude unknown cells from all templates',
    default=False,
)
@click.option(
    '--exclude-input',
    is_flag=True,
    help='exclude input prompts from all templates',
    default=False,
)
@click.option(
    '--exclude-output',
    is_flag=True,
    help='exclude output prompts from all templates',
    default=False,
)
@click.option(
    '--kwarg',
    'kwargs',
    multiple=True,
    help='any additional parameters',
    type=(str, str),
)
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
    kwargs,
):
    if output is None:
        output = os.path.splitext(notebook_path)[0] + '.html'
    nb = Notebook.read(notebook_path)
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
        **dict(kwargs),
    )


@convert.command(help='Exports to a markdown document (.md)')
@click.argument('notebook_path')
@click.option('--output', '-o', help='path to export to', default=None)
@click.option(
    '--template-name', '-t', help='the name of the template to use', default=None
)
@click.option(
    '--exclude-code-cell',
    is_flag=True,
    help='exclude code cells from all templates',
    default=False,
)
@click.option(
    '--exclude-markdown',
    is_flag=True,
    help='exclude markdown cells from all templates',
    default=False,
)
@click.option(
    '--exclude-raw',
    is_flag=True,
    help='exclude unknown cells from all templates',
    default=False,
)
@click.option(
    '--exclude-unknown',
    is_flag=True,
    help='exclude unknown cells from all templates',
    default=False,
)
@click.option(
    '--exclude-input',
    is_flag=True,
    help='exclude input prompts from all templates',
    default=False,
)
@click.option(
    '--exclude-output',
    is_flag=True,
    help='exclude output prompts from all templates',
    default=False,
)
@click.option(
    '--kwarg',
    'kwargs',
    multiple=True,
    help='any additional parameters',
    type=(str, str),
)
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
    kwargs,
):
    if output is None:
        output = os.path.splitext(notebook_path)[0] + '.md'
    nb = Notebook.read(notebook_path)
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
        **dict(kwargs),
    )


@convert.command(help='Exports a Python code file.')
@click.argument('notebook_path')
@click.option('--output', '-o', help='path to export to', default=None)
@click.option(
    '--template-name', '-t', help='the name of the template to use', default=None
)
@click.option(
    '--kwarg',
    'kwargs',
    multiple=True,
    help='any additional parameters',
    type=(str, str),
)
def py(notebook_path, output, template_name, kwargs):
    if output is None:
        output = os.path.splitext(notebook_path)[0] + '.py'
    nb = Notebook.read(notebook_path)
    selector = get_selector()

    nb.select(selector).to_py(output, template_name=template_name, **dict(kwargs))


@convert.command(help='Exports HTML slides with reveal.js')
@click.argument('notebook_path')
@click.option('--output', '-o', help='path to export to', default=None)
@click.option(
    '--template-name', '-t', help='the name of the template to use', default=None
)
@click.option(
    '--exclude-code-cell',
    is_flag=True,
    help='exclude code cells from all templates',
    default=False,
)
@click.option(
    '--exclude-markdown',
    is_flag=True,
    help='exclude markdown cells from all templates',
    default=False,
)
@click.option(
    '--exclude-raw',
    is_flag=True,
    help='exclude unknown cells from all templates',
    default=False,
)
@click.option(
    '--exclude-unknown',
    is_flag=True,
    help='exclude unknown cells from all templates',
    default=False,
)
@click.option(
    '--exclude-input',
    is_flag=True,
    help='exclude input prompts from all templates',
    default=False,
)
@click.option(
    '--exclude-output',
    is_flag=True,
    help='exclude output prompts from all templates',
    default=False,
)
@click.option('--theme', help='Name of the reveal.js theme to use.', default='simple')
@click.option(
    '--transition', help='Name of the reveal.js transition to use', default='slide'
)
@click.option(
    '--scroll/--no-scroll',
    type=bool,
    help='enable scrolling within each slide',
    default=True,
)
@click.option(
    '--kwarg',
    'kwargs',
    multiple=True,
    help='any additional parameters',
    type=(str, str),
)
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
    kwargs,
):
    if output is None:
        output = os.path.splitext(notebook_path)[0] + '.slides.html'
    nb = Notebook.read(notebook_path)
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
        **dict(kwargs),
    )
