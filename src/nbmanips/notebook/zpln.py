from __future__ import annotations

import json
from pathlib import Path

from nbmanips.notebook.ipynb import get_nb_from_dict
from nbmanips.notebook.notebook import Notebook

try:
    import pandas as pd
except ImportError:
    pd = None


class ZPLN(Notebook):
    def __new__(
        cls, path: str, name: str | None = None, encoding: str = "utf-8"
    ) -> Notebook:
        return Notebook.read_zpln(path, encoding=encoding, name=name)


# -- Constants --
# --- READERS Constants ---
ZPLN_PREFIXES = {
    "python": {"%python", "%pyspark", "%spark.pyspark"},
}


def read_zpln(
    notebook_path: str, version: int = 4, encoding: str = "utf-8"
) -> tuple[str, dict]:
    from io import StringIO

    zep_nb = json.loads(Path(notebook_path).read_text(encoding=encoding))
    name = zep_nb.get("name", Path(notebook_path).stem)
    language = zep_nb.get("defaultInterpreterGroup", "python")
    language_prefixes = ZPLN_PREFIXES.get(language, {"%" + language})
    notebook = {
        "metadata": {"language_info": {"name": language}},
        "nbformat": 4,
        "nbformat_minor": 4,
        "cells": [],
    }

    for paragraph in zep_nb.get("paragraphs", []):
        paragraph_config = paragraph.get("config", {})
        source_hidden = paragraph_config.get("editorHide", False)
        outputs_hidden = paragraph_config.get("tableHide", False)
        cell = {
            "metadata": {
                "collapsed": source_hidden and outputs_hidden,
                "jupyter": dict(
                    source_hidden=source_hidden, outputs_hidden=outputs_hidden
                ),
            }
        }
        title = paragraph.get("title", None)
        if title:
            cell["metadata"]["name"] = title

        source = paragraph.get("text", "")
        prefix = source.split()[0].strip() if source.startswith("%") else None
        suffix = "\n".join(source.split("\n")[1:]) if prefix else source

        if prefix is not None and prefix.startswith("%md"):
            cell["source"] = suffix
            cell["cell_type"] = "markdown"
            notebook["cells"].append(cell)
            continue

        if prefix is None or prefix in language_prefixes:
            cell["source"] = suffix
        else:
            cell["source"] = source

        cell["cell_type"] = "code"
        cell["outputs"] = []
        if (
            paragraph.get("results", None)
            and paragraph["results"].get("code", None).upper() != "ERROR"
        ):
            for result in paragraph["results"].get("msg", []):
                result_type = result.get("type", "TEXT").upper()
                if result_type == "TEXT":
                    data = result.get("data", "")
                    cell["outputs"].append(
                        {"output_type": "stream", "text": data, "name": "stdout"}
                    )
                elif result_type == "TABLE":
                    data = result.get("data", "")
                    if pd is None:
                        cell["outputs"].append(
                            {"output_type": "stream", "text": data, "name": "stdout"}
                        )
                    else:
                        data = pd.read_csv(StringIO(data), sep="\t").to_html()
                        cell["outputs"].append(
                            {
                                "output_type": "display_data",
                                "data": {"text/html": data},
                                "metadata": {},
                            }
                        )
                elif result_type in "HTML":
                    data = result.get("data", "")
                    cell["outputs"].append(
                        {
                            "output_type": "display_data",
                            "data": {"text/html": data},
                            "metadata": {},
                        }
                    )

        cell["execution_count"] = None

        notebook["cells"].append(cell)

    nb_node = get_nb_from_dict(notebook, as_version=version)
    return name, dict(nb_node)
