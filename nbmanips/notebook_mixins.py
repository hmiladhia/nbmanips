try:
    import nbconvert
except ImportError:
    nbconvert = None

from nbmanips.notebook_base import NotebookBase
from nbmanips.selector import is_new_slide, has_slide_type, has_output_type


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

    def delete(self, selector, *args, **kwargs):
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

    def auto_slide(self, max_cells_per_slide=3, max_images_per_slide=1, *_, delete_empty=True):
        # Delete Empty
        if delete_empty:
            self.delete('is_empty')

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

    def to_slides(self, path):
        notebook_node = self.to_notebook_node()
        exporter = nbconvert.SlidesExporter()

        (body, resources) = exporter.from_notebook_node(notebook_node)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(body)
