from types import ModuleType

import click

from nbmanips import __version__
from nbmanips.cli import collection, explore, transform
from nbmanips.cli.convert import convert
from nbmanips.cli.select import select

__all__ = ["nbmanips"]


@click.group()
@click.version_option(__version__, prog_name="nbmanips")
def nbmanips() -> None:
    pass


def _add_commands(module: ModuleType) -> None:
    for command in module.__all__:
        command_name = command.strip("_").replace("_", "-")
        nbmanips.add_command(getattr(module, command), command_name)


nbmanips.add_command(convert)
nbmanips.add_command(select)
_add_commands(explore)
_add_commands(transform)
_add_commands(collection)


if __name__ == "__main__":
    nbmanips()
