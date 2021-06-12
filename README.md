# nbmanips
[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/tterb/atomic-design-ui/blob/master/LICENSEs)

A collections of utilities to manipulate IPython/Jupyter Notebooks via a python script.

## Usage/Examples
### Basic usage
A simple Example of using nbmanips:
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
- A slice object
- A predefined selector
- A function that takes a Cell object and returns True if the cell should be selected
 
### Export Format
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
