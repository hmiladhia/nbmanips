from pathlib import Path

import click
import cloudpickle


def export(nb, output, force=False):
    if not force:
        if Path(output).exists():
            click.confirm(f'"{output}" already exists. Do you want to overwrite it?', abort=True)
    nb.to_ipynb(output)


def get_selector():
    binary_stream = click.get_binary_stream('stdin')
    if binary_stream.isatty():
        return None

    stream = binary_stream.read()
    if not stream:
        return None

    return cloudpickle.loads(stream)
