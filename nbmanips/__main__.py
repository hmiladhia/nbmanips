import click

from nbmanips import __version__
from nbmanips.cli.select import select
from nbmanips.cli.convert import convert
import nbmanips.cli.explore as explore
import nbmanips.cli.transform as transform
import nbmanips.cli.collection as collection

__all__ = [
    'nbmanips'
]


@click.group()
@click.version_option(__version__, prog_name='nbmanips')
def nbmanips():
    pass


def _add_commands(module):
    for command in module.__all__:
        command_name = command.strip('_').replace('_', '-')
        nbmanips.add_command(getattr(module, command), command_name)


nbmanips.add_command(convert)
nbmanips.add_command(select)
_add_commands(explore)
_add_commands(transform)
_add_commands(collection)


if __name__ == '__main__':
    nbmanips()
