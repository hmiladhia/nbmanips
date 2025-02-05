from __future__ import annotations

import json
from pathlib import Path

from nbmanips.notebook.ipynb import get_nb_from_dict
from nbmanips.notebook.notebook import Notebook


class DBC(Notebook):
    def __new__(
        cls,
        path: str,
        filename: str | None = None,
        encoding: str = "utf-8",
        name: str | None = None,
    ) -> Notebook:
        return Notebook.read_dbc(path, filename=filename, encoding=encoding, name=name)


def _get_dbc_dict(
    notebook_path: str, filename: str | None = None, encoding: str = "utf-8"
) -> dict:
    import zipfile

    if not zipfile.is_zipfile(notebook_path):
        if filename is not None or filename != Path(notebook_path).name:
            raise ValueError(f"Invalid filename: {filename}")

        return json.loads(Path(notebook_path).read_text(encoding=encoding))

    with zipfile.ZipFile(notebook_path, "r") as zf:
        if filename is None:
            names = zf.namelist()
            files = [name for name in names if not name.endswith("/")]
            if len(files) > 1:
                raise ValueError(
                    f"Multiple Notebooks in archive: {files}\nSpecify the notebook filename."
                )
            filename = files[0]

        return json.loads(zf.read(filename).decode(encoding))


def read_dbc(
    notebook_path: str,
    version: int = 4,
    filename: str | None = None,
    encoding: str = "utf-8",
) -> tuple[str, dict]:
    from html2text import html2text

    dbc_nb = _get_dbc_dict(notebook_path, filename, encoding)

    name = dbc_nb.get("name", Path(notebook_path).stem)
    language = dbc_nb.get("language", Path(notebook_path).suffix.lstrip(".").lower())
    language_prefix = f"%{language}" if language != "python" else "%py"
    notebook = {
        "metadata": {"language_info": {"name": language}},
        "nbformat": 4,
        "nbformat_minor": 4,
        "cells": [],
    }

    for command in dbc_nb.get("commands", []):
        cell = {"metadata": {"collapsed": command.get("collapsed", False)}}
        source = command.get("command", "")
        prefix = source.split("\n")[0].strip() if source.startswith("%") else None
        suffix = "\n".join(source.split("\n")[1:]) if prefix else source

        if prefix is not None and prefix.startswith("%md"):
            cell["source"] = suffix
            cell["cell_type"] = "markdown"
            notebook["cells"].append(cell)
            continue

        if prefix is None or prefix == language_prefix:
            cell["source"] = suffix
        else:
            cell["source"] = source

        cell["cell_type"] = "code"
        cell["outputs"] = []
        if (
            command.get("results", None)
            and command["results"].get("type", None) == "html"
        ):
            html = command["results"].get("data", "")
            cell["outputs"].append(
                {
                    "output_type": "display_data",
                    "data": {"text/html": html},
                    "metadata": {},
                }
            )

        error_summary = html2text(command.get("errorSummary", None) or "")
        error = html2text(command.get("error", None) or "")
        if error_summary or error:
            if ":" in error_summary:
                ename, evalue = error_summary.split(":", 1)
            else:
                ename, evalue = "", error_summary
            cell["outputs"].append(
                {
                    "output_type": "error",
                    "ename": ename,
                    "evalue": evalue,
                    "traceback": error.split("\n"),
                }
            )

        cell["execution_count"] = None

        notebook["cells"].append(cell)

    nb_node = get_nb_from_dict(notebook, as_version=version)
    return name, dict(nb_node)
