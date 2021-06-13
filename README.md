# nbmanips
![PyPI - License](https://img.shields.io/pypi/l/nbmanips)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/nbmanips)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/nbmanips)
![PyPI](https://img.shields.io/pypi/v/nbmanips)

A collections of utilities to manipulate IPython/Jupyter Notebooks via a python script.

## Usage/Examples
### Basic usage
A simple example of using nbmanips:

```python
from nbmanips import Notebook

# Read ipynb file
nb = Notebook.read_ipynb("my_notebook.ipynb")

# delete empty cells
nb.delete("empty")

# save ipynb file
nb.to_ipynb("new_notebook.ipynb")
```

Examples of operations you can perform on a Notebook:

- `replace`: Replace matching text in the selected cells
- `tag`: Add metadata to the selected cells
- `erase`: Erase the content of the selected cells
- `delete`: Delete the selected cells
- `keep`: Kepp the selected cells

### Selectors
To select cells on which to apply the previous operations, you can use:

- The cell number

```python
nb.show(0)
```
- A slice object

```python
selected_cells = slice(1, 6, 2)

nb.show(selected_cells)
```
- A predefined selector. Available predefined selectors are the following:

    - `code_cells` / `markdown_cells` / `raw_cells`: Selects cells with the given type
    - `contains`: Selects Cells containing a certain text.
    - `is_empty` / `empty`: Selects empty cells
    - `has_output`: Checks if the cell has any output
    - `has_output_type`: Select cells that have a given output_type
    - `has_slide_type`: Select cells that have a given slide type
    - `is_new_slide`: Selects cells where a new slide/subslide starts

```python
# Show Markdown Cells
nb.show('markdown_cells')

# Show Cells containing the equal sign
nb.show('contains', '=')
```



- A function that takes a Cell object and returns True if the cell should be selected
```python
# Show Cells with length > 10
nb.show(lambda cell: len(cell.source) > 10)
```
- A list of Selectors
```python
# Show Empty Markdown Cells
nb.show(['markdown_cells', 'is_empty'])

# Show Markdown or Code Cells
nb.show(['markdown_cells', 'code_cells'], type='or')
```
 
### Export Formats
You can export the notebooks to these formats:

- to_ipynb
- to_html
- to_slides (using reveal.js)
- to_md (to markdown)
- to_py (to python)
- to_text (textual representation of the notebook)

### Slide manipulations
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
  
## Roadmap

- Add Custom Templates

- Add CLI
