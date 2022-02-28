# nbmanips
![PyPI](https://img.shields.io/pypi/v/nbmanips)
![PyPI - License](https://img.shields.io/pypi/l/nbmanips)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/nbmanips)

![Tests](https://github.com/hmiladhia/nbmanips/actions/workflows/tests.yml/badge.svg)
[![codecov](https://codecov.io/gh/hmiladhia/nbmanips/branch/main/graph/badge.svg)](https://codecov.io/gh/hmiladhia/nbmanips)

A collections of utilities to manipulate IPython/Jupyter Notebooks via a python script.

## I - Usage/Examples
### 1 - Basic usage
A simple example of using nbmanips:

```python
from nbmanips import Notebook

# Read ipynb file
nb = Notebook.read_ipynb("my_notebook.ipynb")

# delete empty cells
nb.select("empty").delete()

# save ipynb file
nb.to_ipynb("new_notebook.ipynb")
```

Examples of operations you can perform on a Notebook:

- `replace`: Replace matching text in the selected cells
- `tag`: Add metadata to the selected cells
- `erase`: Erase the content of the selected cells
- `delete`: Delete the selected cells
- `keep`: Kepp the selected cells

### 2 - Selectors
To select cells on which to apply the previous operations, you can use:

- The cell number

```python
nb[0].show()

# OR
nb.select(0).show()
```
- A slice object

```python
nb[1:6:2].show()

# OR
selected_cells = slice(1, 6, 2)

nb.select(selected_cells).show()
```
- A predefined selector. Available predefined selectors are the following:

    - `code_cells` / `markdown_cells` / `raw_cells`: Selects cells with the given type
    - `contains`: Selects Cells containing a certain text.
    - `is_empty` / `empty`: Selects empty cells
    - `has_output`: Checks if the cell has any output
    - `has_output_type`: Select cells that have a given output_type
    - `has_slide_type`: Select cells that have a given slide type
    - `is_new_slide`: Selects cells where a new slide/subslide starts
    - `has_byte_size`: Selects cells with byte size within a given range of values.

```python
# Show Markdown Cells
nb.select('markdown_cells').show()

# Show Cells containing the equal sign
nb.select('contains', '=').show()
```



- A function that takes a Cell object and returns True if the cell should be selected
```python
# Show Cells with length > 10
nb.select(lambda cell: len(cell.source) > 10).show()
```
- A list of Selectors
```python
# Show Empty Markdown Cells
nb.select(['markdown_cells', 'is_empty']).show()

# Show Markdown or Code Cells
nb.select(['markdown_cells', 'code_cells'], type='or').show()
```

### 3 - Export Formats
You can export the notebooks to these formats:

- to_ipynb
- to_dbc
- to_html
- to_slides (using reveal.js)
- to_md (to markdown)
- to_py (to python)
- to_text (textual representation of the notebook)

### 4 - Slide manipulations
You can manipulate the slides by tagging which cells to keep and which to skip.
The following actions are available:

- set_slide
- set_subslide
- set_skip
- set_fragment
- set_notes

A neat trick is to use `auto_slide` method to automatically create slides out of your notebook:
```python
from nbmanips import Notebook

# Read ipynb file
nb = Notebook.read_ipynb("my_notebook.ipynb")

# Automatically create slides
nb.auto_slide()

# Export to Reveal.js slides (HTML)
nb.to_slides("new_slides.slides.html", theme='beige')
```

## II - CLI
### 1 - Show a notebook
To get a readable representation of the notebook
```bash
nb show my_notebook.ipynb
```

Other options are available. For example, you can customize the style, weather to truncate the output of cells:
```bash
nb show -s double -t 100 my_notebook.ipynb
```

To show a subset of the notebook cells, you can perform a select operation:
```bash
nb select 0:3 | nb show my_notebook.ipynb

# Or if you're using negative indexes ( to show the last 3 cells )
nb select [-3:] | nb show my_notebook.ipynb
```
### 2 - Basic usage
A simple example of using nbmanips via the cli:

```bash
# delete empty cells
nb select empty | nb delete my_notebook.ipynb --output new_notebook.ipynb

# Or equivalently:
nbmanips select empty | nbmanips delete my_notebook.ipynb --output new_notebook.ipynb
```

You could also show the table of contents of a certain notebook:
```bash
nb toc nb.ipynb
```

Or split a notebook into multiple notebooks:

```bash
nb split nb.ipynb 5,9
```

### 3 - Export Formats
You can convert a notebook to the following formats:

- html: `nb convert html my_notebook.ipynb --output my_notebook.html`
- slides (using reveal.js): `nb convert slides my_notebook.ipynb --output my_notebook.slides.html`
- md (to markdown): `nb convert md my_notebook.ipynb --output my_notebook.md`
- py (to python): `nb convert py my_notebook.ipynb --output my_notebook.py`

### 4 - Slide manipulations
```bash
# Automatically set slides
nb auto-slide -f my_notebook.ipynb

# Generate a my_notebook.slides.html file
nb convert slides my_notebook.ipynb
```

Or if you do not wish to modify your original notebook:
```bash
# Automatically set slides
nb auto-slide my_notebook.ipynb -o my_temp_notebook.ipynb

# Generate a my_notebook.slides.html file
nb convert slides my_temp_notebook.ipynb -o my_notebook.slides.html
```

If you need more details you can check the --help option:
```
nbmanips --help
```

## III - Optional Requirements

There are optional requirements you may want to install to render images in the terminal.
The results, however, are not always convincing.
If you want to enable this feature, you can just run the following command:

```bash
pip install nbmanips[images]
```

## Roadmap

- Add Custom Templates
