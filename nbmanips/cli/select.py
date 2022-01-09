from functools import reduce

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


def get_params(ctx):
    kwargs = dict(ctx.parent.params['kwargs'])
    kwargs.update(ctx.params['kwargs'])
    return {
        'or_': ctx.parent.params['or_'] or ctx.params['or_'],
        'invert': ctx.parent.params['invert'] or ctx.params['invert'],
        'kwargs': kwargs
    }


def select_kwargs(func):
    decorators = [
        click.option('--kwarg', 'kwargs', multiple=True, type=(str, str)),
        click.option('--or', '-o', 'or_', is_flag=True, default=False),
        click.option('--invert', '-i', is_flag=True, default=False),
        func
    ]

    return reduce(lambda f, g: g(f), decorators[::-1])


# https://click.palletsprojects.com/en/8.0.x/commands/


@click.group(cls=SelectGroup)
@select_kwargs
def select(**_):
    pass


@click.command()
@click.argument('selector', required=True)
@click.argument('arguments', nargs=-1, required=False)
@select_kwargs
@click.pass_context
def select_unknown(ctx, selector, arguments, **_):
    if selector.isdigit():
        selector = int(selector)
    elif selector.replace(':', '').isdigit():
        selector = slice(*[int(p) for p in selector.split(':')])

    params = get_params(ctx)

    _select_unknown(selector, arguments, **params)


@select.command(name='has_output_type', help='Select cells that have a given output_type')
@click.argument('output_type', nargs=-1, required=True)
@select_kwargs
@click.pass_context
def has_output_type(ctx, output_type, **_):
    arguments = [set(output_type)]

    params = get_params(ctx)
    _select_unknown('has_output_type', arguments, **params)


def _select_unknown(selector, arguments, kwargs, or_, invert):
    sel = Selector(selector, *arguments, **kwargs)
    if invert:
        sel = ~sel

    piped_selector = get_selector()
    if piped_selector is not None:
        sel = (piped_selector | sel) if or_ else (piped_selector & sel)

    click.echo(cloudpickle.dumps(sel))
