import click
import cloudpickle

from nbmanips.selector import Selector


def get_selector():
    if not click.get_text_stream('stdin').isatty():
        stream = click.get_binary_stream('stdin').read()
        selector = cloudpickle.loads(stream)
    else:
        selector = None
    return selector


@click.command()
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
