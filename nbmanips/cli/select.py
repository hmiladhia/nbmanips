import click
import cloudpickle
from click import Group

from nbmanips.selector import Selector

__all__ = [
    'select',
    'get_selector'
]


class SelectGroup(Group):
    def resolve_command(self, ctx, args):
        cmd_name, cmd, args = super().resolve_command(ctx, args)
        if cmd is select_unknown:
            args = [cmd_name] + args
        return cmd_name, cmd, args

    def get_command(self, ctx, cmd_name):
        return self.commands.get(cmd_name, select_unknown)

    def list_commands(self, ctx):
        commands = set(self.commands)
        commands |= set(Selector.default_selectors)
        return sorted(commands)


def get_selector():
    binary_stream = click.get_binary_stream('stdin')
    if binary_stream.isatty():
        return None

    stream = binary_stream.read()
    if not stream:
        return None

    return cloudpickle.loads(stream)


# https://click.palletsprojects.com/en/8.0.x/commands/


@click.group(cls=SelectGroup)
def select():
    pass


@click.command()
@click.argument('selector', required=True)
@click.argument('arguments', nargs=-1, required=False)
@click.option('--kwarg', 'kwargs', multiple=True, type=(str, str))
@click.option('--or', 'or_', is_flag=True, default=False)
@click.option('--invert', '-i', is_flag=True, default=False)
def select_unknown(selector, arguments, kwargs, or_, invert):
    if selector.isdigit():
        selector = int(selector)
    elif selector.replace(':', '').isdigit():
        selector = slice(*[int(p) for p in selector.split(':')])

    _select_unknown(selector, arguments, kwargs, or_, invert)


@select.command(name='has_output_type', help='Select cells that have a given output_type')
@click.argument('arguments', nargs=-1, required=False)
@click.option('--kwarg', 'kwargs', multiple=True, type=(str, str))
@click.option('--or', 'or_', is_flag=True, default=False)
@click.option('--invert', '-i', is_flag=True, default=False)
def has_output_type(arguments, kwargs, or_, invert):
    _select_unknown('has_output_type', arguments, kwargs, or_, invert)


def _select_unknown(selector, arguments, kwargs, or_, invert):
    sel = Selector(selector, *arguments, **dict(kwargs))
    if invert:
        sel = ~sel

    piped_selector = get_selector()
    if piped_selector is not None:
        sel = (piped_selector | sel) if or_ else (piped_selector & sel)

    click.echo(cloudpickle.dumps(sel))
