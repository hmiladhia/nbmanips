import warnings
from pathlib import Path

import click
import cloudpickle


def export(nb, input_path, output_path, force=False):
    default_output = output_path is None
    output_path = input_path if output_path is None else output_path
    if not force and Path(output_path).exists():
        click.echo(
            f'Notebook "{output_path}" already exists.' ' Use --force to overwrite'
        )
        raise click.Abort()

    if output_path.lower().endswith('.dbc'):
        return nb.to_dbc(output_path)

    if output_path.lower().endswith('.zpln'):
        if default_output:
            output_path = Path(output_path).resolve()
            root_path = output_path.parent
            output_path = str(root_path / (root_path.stem + '.ipynb'))
        else:
            warnings.warn('Zeppelin Notebooks exports are not supported.')

    nb.to_ipynb(output_path)


def get_selector():
    binary_stream = click.get_binary_stream('stdin')
    if binary_stream.isatty():
        return None

    stream = binary_stream.read()
    if not stream:
        return None

    return cloudpickle.loads(stream)
