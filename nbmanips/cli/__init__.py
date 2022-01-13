from pathlib import Path

import click
import cloudpickle


def export(nb, output, force=False):
    if not force and Path(output).exists():
        click.echo(f'Notebook "{output}" already exists. Use --force to overwrite')
        raise click.Abort()
    nb.to_ipynb(output)


def get_selector():
    binary_stream = click.get_binary_stream('stdin')
    if binary_stream.isatty():
        return None

    stream = binary_stream.read()
    if not stream:
        return None

    return cloudpickle.loads(stream)
