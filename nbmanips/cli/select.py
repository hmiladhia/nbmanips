import copy
import re
from functools import reduce

import click
import cloudpickle
from click import Group

from nbmanips.cli import get_selector
from nbmanips.selector import DefaultSelector, Selector

__all__ = [
    'select',
]


def _is_digit(selector):
    match = re.fullmatch(r'(-?\d+)', selector)

    if match is None:
        match = re.fullmatch(r'\[(-?\d+)\]', selector)

    if match is None:
        return None
    return match.group(1)


def _is_slice(selector):
    match = re.fullmatch(r'((-?\d+))?(:(-?\d+)?)?(:(-?\d+)?)?', selector)

    if match is None:
        match = re.fullmatch(r'\[((-?\d+))?(:(-?\d+)?)?(:(-?\d+)?)?\]', selector)

    if match is None:
        return None

    ret = []
    for el in match.groups()[1::2]:
        if el is not None:
            el = int(el)
        ret.append(el)
    return ret


class SelectGroup(Group):
    @property
    def dynamic_commands(self):
        return DefaultSelector.default_selectors

    def resolve_command(self, ctx, args):
        cmd_name, cmd, new_args = super().resolve_command(ctx, args)
        if cmd is None:
            return cmd_name, cmd, new_args

        if cmd_name not in self.list_commands(ctx):
            cmd_name = 'INDEX/SLICE'
        elif cmd_name in self.commands:
            args = new_args

        return cmd_name, cmd, args

    def get_command(self, ctx, cmd_name):
        cmd = self.commands.get(cmd_name)

        if cmd is not None:
            return cmd

        if cmd_name in self.dynamic_commands:
            cmd = copy.deepcopy(select_unknown)

            select_func = self.dynamic_commands[cmd_name]
            short_description = select_func.__doc__.strip().split('\n')[0]
            cmd.help = short_description
        elif _is_slice(cmd_name):
            cmd = copy.deepcopy(select_unknown)
        elif cmd_name == '[INDEX/SLICE]':
            cmd = copy.deepcopy(select_unknown)
            cmd.help = 'Selects Cells based on their index'

        return cmd

    def list_commands(self, ctx):
        commands = set(self.commands)
        commands |= set(self.dynamic_commands)
        commands |= {'[INDEX/SLICE]'}
        return sorted(commands)


def get_params(ctx, **kwargs):
    return {
        'or_': ctx.parent.params['or_'] or ctx.params['or_'],
        'invert': ctx.parent.params['invert'] or ctx.params['invert'],
        'kwargs': kwargs,
    }


def select_params(func):
    decorators = [
        click.option('--or', '-o', 'or_', is_flag=True, default=False),
        click.option('--invert', '-i', is_flag=True, default=False),
        func,
    ]

    return reduce(lambda f, g: g(f), decorators[::-1])


@click.group(cls=SelectGroup)
@select_params
def select(**_):
    pass


@click.command()
@click.argument('selector', required=True)
@click.argument('arguments', nargs=-1, required=False)
@click.option('--kwarg', 'kwargs', multiple=True, type=(str, str))
@select_params
@click.pass_context
def select_unknown(ctx, selector, arguments, kwargs, **_):
    if selector == '[INDEX/SLICE]':
        raise ValueError('Provide an index. Example: nb select [-3:-1]')
    digit_match = _is_digit(selector)
    slice_match = _is_slice(selector)
    if digit_match:
        selector = int(digit_match)
    elif slice_match:
        selector = slice(*slice_match)

    params = get_params(ctx, **dict(kwargs))

    _select_unknown(selector, arguments, **params)


@select.command(
    name='has_output_type', help='Select cells that have a given output_type'
)
@click.argument('output_type', nargs=-1, required=True)
@select_params
@click.pass_context
def has_output_type(ctx, output_type, **_):
    arguments = [set(output_type)]

    params = get_params(ctx)
    _select_unknown('has_output_type', arguments, **params)


@select.command(name='has_slide_type', help='Select cells that have a given slide type')
@click.argument('slide_type', nargs=-1, required=True)
@select_params
@click.pass_context
def has_slide_type(ctx, slide_type, **_):
    arguments = [set(slide_type)]

    params = get_params(ctx)
    _select_unknown('has_slide_type', arguments, **params)


@select.command(name='contains', help='Selects Cells containing a certain text.')
@click.argument('text', type=str, required=True)
@click.option('--case', '-c', is_flag=True, default=False)
@click.option('--include-output', '-n', 'output', is_flag=True, default=False)
@click.option('--regex', '-r', is_flag=True, default=False)
@select_params
@click.pass_context
def contains(ctx, text, case, output, regex, **_):
    params = get_params(
        ctx,
        case=case,
        output=output,
        regex=regex,
    )

    _select_unknown('contains', [text], **params)


def _select_unknown(selector, arguments, kwargs, or_, invert):
    sel = Selector(selector, *arguments, **kwargs)
    if invert:
        sel = ~sel

    piped_selector = get_selector()
    if piped_selector is not None:
        sel = (piped_selector | sel) if or_ else (piped_selector & sel)

    click.echo(cloudpickle.dumps(sel), nl=False)
