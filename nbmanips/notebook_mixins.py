import copy
import json

try:
    import nbformat
except ImportError:
    nbformat = None

try:
    import nbconvert
except ImportError:
    nbconvert = None

from nbmanips import Cell
from nbmanips import Selector
from nbmanips.selector import is_new_slide, has_slide_type, has_output_type


class NotebookBase:
    def __init__(self, content, name=None):
        self._nb = copy.deepcopy(content)
        self.name = name

    def __add__(self, other: 'NotebookBase'):
        # Copying the notebook
        nb = copy.deepcopy(self._nb)

        # Concatenating the notebooks
        nb['cells'] = nb['cells'] + other._nb['cells']
        return self.__class__(nb)

    def __getitem__(self, item):
        return self._nb[item]

    def __setitem__(self, item, value):
        self._nb[item] = value

    def __len__(self):
        if self._nb is None or 'cells' not in self._nb:
            return 0
        return len(self._nb['cells'])

    def __repr__(self):
        if self.name:
            return f'<Notebook "{self.name}">'
        else:
            return f"<Notebook>"

    def __str__(self):
        return '\n'.join(str(Cell(cell, i, self._nb)) for i, cell in enumerate(self.cells))

    def iter_cells(self, selector=None, *args, **kwargs):
        return Selector(selector, *args, **kwargs).iter_cells(self._nb)

    def iter_neg_cells(self, selector, *args, **kwargs):
        return Selector(selector, *args, **kwargs).iter_cells(self._nb, neg=True)

    def to_notebook_node(self):
        if nbformat:
            return nbformat.reads(json.dumps(self._nb), as_version=4)
        else:
            raise ModuleNotFoundError('You need to pip install nbformat to get NotebookNode object')

    def to_html(self, path, template=None):
        notebook_node = self.to_notebook_node()
        slides_exporter = nbconvert.HTMLExporter()

        if template is not None:
            NotImplemented('Template is not supported yet')

        (body, resources) = slides_exporter.from_notebook_node(notebook_node)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(body)


    @property
    def cells(self):
        return self._nb['cells']


class SlideShowMixin(NotebookBase):
    def mark_slideshow(self):
        self._nb['metadata']["celltoolbar"] = "Slideshow"

    def set_slide(self, selector, *args, **kwargs):
        self.tag_slide('slide', selector, *args, **kwargs)

    def set_skip(self, selector, *args, **kwargs):
        self.tag_slide('skip', selector, *args, **kwargs)

    def set_subslide(self, selector, *args, **kwargs):
        self.tag_slide('subslide', selector, *args, **kwargs)

    def set_fragment(self, selector, *args, **kwargs):
        self.tag_slide('fragment', selector, *args, **kwargs)

    def set_notes(self, selector, *args, **kwargs):
        self.tag_slide('notes', selector, *args, **kwargs)

    def tag_slide(self, tag, selector, *args, **kwargs):
        assert tag in {'-', 'skip', 'slide', 'subslide', 'fragment', 'notes'}
        self.tag('slideshow', {'slide_type': tag}, selector, *args, **kwargs)

    def tag(self, tag_key, tag, selector, *args, **kwargs):
        raise NotImplemented()

    def max_cells_per_slide(self, n_cells=3, n_images=1):
        cells_count = 0
        img_count = 0
        for cell in self.iter_cells():
            is_image = has_output_type(cell, 'image/png')
            if is_new_slide(cell):
                cells_count = 1
                img_count = 0
            elif has_slide_type(cell, {'skip', 'fragment', 'notes'}):
                # Don't count
                pass
            else:
                cells_count += 1
            if is_image:
                img_count += 1

            if (n_cells is not None and cells_count > n_cells) or (n_images is not None and img_count > n_images):
                if 'slideshow' in cell.cell['metadata']:
                    cell.metadata['slideshow']['slide_type'] = 'subslide'
                else:
                    cell.metadata['slideshow'] = {'slide_type': 'subslide'}
                cells_count = 1
                img_count = 1 if is_image else 0

    def auto_slide(self, max_cells_per_slide=3, max_images_per_slide=1):
        # Each title represents
        self.set_slide(['is_markdown', 'contains'], [], '#')

        # Create a new slide only
        for cell in reversed(list(self.iter_cells())):
            if cell.num > 0 and is_new_slide(cell.previous_cell):
                if 'slideshow' in cell.cell['metadata']:
                    cell.metadata['slideshow']['slide_type'] = '-'
                else:
                    cell.metadata['slideshow'] = {'slide_type': '-'}

        # Set max cells per slide
        self.max_cells_per_slide(max_cells_per_slide, max_images_per_slide)

    def to_slides(self, path, template=None):
        notebook_node = self.to_notebook_node()
        slides_exporter = nbconvert.SlidesExporter()

        if template is not None:
            NotImplemented('Template is not supported yet')

        (body, resources) = slides_exporter.from_notebook_node(notebook_node)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(body)
