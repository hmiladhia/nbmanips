import re
from typing import Callable, ClassVar, Dict, Optional, Union

from nbmanips.cell import Cell, MarkdownCell

from .callable_selector import CallableSelector


class DefaultSelector(CallableSelector):
    default_selectors: ClassVar[Dict[str, Callable]] = {}

    def __init__(self, selector: str, *args, **kwargs):
        # TODO: use signature ?
        callable_selector = self.default_selectors[selector]
        super(DefaultSelector, self).__init__(callable_selector, *args, **kwargs)

    @classmethod
    def register_selector(cls, key: str, selector: Callable[..., bool]) -> None:
        cls.default_selectors[key] = selector


# -- Default Selectors --
def contains(
    cell: Cell, text, case=True, output=False, regex=False, flags: int = 0
) -> bool:
    """
    Selects Cells containing a certain text.

    :param cell: Cell object to select
    :param text: a string to find in cell
    :param case: True if the search is case sensitive
    :type case: default True
    :param output: True if you want the search in the output of the cell too
    :type output: default False
    :param regex: boolean whether to use regex or not
    :param flags: flags used if regex is set to True
    :type flags: int
    :return: a bool object (True if cell should be selected)
    """
    return cell.contains(text, case=case, output=output, regex=regex, flags=flags)


def has_match(cell: Cell, regex, output=False) -> bool:
    """
    Selects Cells that match a certain regex.

    :param cell: Cell object to select
    :param text: a string to find in cell
    :param case: True if the search is case sensitive
    :type case: default True
    :param output: True if you want the search in the output of the cell too
    :type output: default False
    :param regex: boolean whether to use regex or not
    :return: a bool object (True if cell should be selected)
    """

    if isinstance(regex, str):
        regex = re.compile(regex)

    return cell.has_match(regex, output=output)


def has_type(cell: Cell, type) -> bool:
    """
    Selects cells with the given type

    :param cell: Cell object to select
    :param type:
    :return: a bool object (True if cell should be selected)
    """
    return cell.type == type


def is_code(cell: Cell) -> bool:
    """
    Selects code cells

    :param cell: Cell object to select
    :return: a bool object (True if cell should be selected)
    """
    return has_type(cell, 'code')


def is_markdown(cell: Cell) -> bool:
    """
    Selects markdown cells

    :param cell: Cell object to select
    :return: a bool object (True if cell should be selected)
    """
    return has_type(cell, 'markdown')


def is_raw(cell: Cell) -> bool:
    """
    Selects raw cells

    :param cell: Cell object to select
    :return: a bool object (True if cell should be selected)
    """
    return has_type(cell, 'raw')


def has_output(cell: Cell, value: bool = True) -> bool:
    """
    Checks if the cell has any output

    :param cell: Cell object to select
    :param value: set to False if you want to select cells with no output
    :return: a bool object (True if cell should be selected)
    """
    return (cell.output != '') == value


def has_output_type(cell: Cell, output_type: Union[set, str]) -> bool:
    """
    Selects cells that have a given output_type

    :param cell: Cell object to select
    :param output_type: Output Type(MIME type) to select: text/plain, text/html, image/png, ...
    :type output_type: str
    :return: a bool object (True if cell should be selected)
    """
    if isinstance(output_type, str):
        output_types = {output_type}
    else:
        output_types = set(output_type)

    return cell.has_output_type(output_types)


def is_empty(cell: Cell) -> bool:
    """
    Selects empty cells

    :param cell: Cell object to select
    :return: a bool object (True if cell should be selected)
    """
    return cell.source == '' and has_output(cell, False)


def has_byte_size(
    cell: Cell,
    min_size=0,
    max_size: Optional[int] = None,
    output_types=None,
    ignore_source=False,
) -> bool:
    """
    Selects cells with byte size less than max_size and more than min_size.

    :param cell: Cell object to select
    :param min_size: int representing the minimum size
    :param max_size: int representing the maximum size
    :param output_types: Output Types(MIME type) to select: text/plain, text/html, image/png, ...
    :type output_types: set
    :param ignore_source: True if you want to get the size of the output only
    :return: a bool object (True if cell should be selected)
    """
    if isinstance(output_types, str):
        output_types = {output_types}

    size = cell.byte_size(output_types, ignore_source)

    return size >= min_size and (max_size is None or size < max_size)


def has_slide_type(cell: Cell, slide_type) -> bool:
    """
    Selects markdown cells that have a given slide type

    :param cell: Cell object to select
    :param slide_type: Slide Type(s): '-', 'skip', 'slide', 'subslide', 'fragment', 'notes'
    :type slide_type: str / set / list
    :return: a bool object (True if cell should be selected)
    """
    if isinstance(slide_type, str):
        slide_type = {slide_type}

    return all(
        f(cell)
        for f in [
            lambda c: 'slideshow' in c.metadata,
            lambda c: 'slide_type' in c.metadata['slideshow'],
            lambda c: c.metadata['slideshow']['slide_type'] in slide_type,
        ]
    )


def has_tag(cell: Cell, tag: str, case=False) -> bool:
    """
    Selects cells that have a certain tag

    :param cell: Cell object to select
    :param tag:
    :type tag: str
    :param case:
    :type case: bool
    :return: a bool object (True if cell should be selected)
    """
    if case:
        return tag in cell.metadata.get('tags', {})
    else:
        return tag.lower() in {
            cell_tag.lower() for cell_tag in cell.metadata.get('tags', {})
        }


def with_css_selector(cell: MarkdownCell, css_selector: str) -> bool:
    """
    Select cells that match a certain CSS Selector

    :param cell: Cell object to select
    :param css_selector: Css selector
    :type css_selector: str
    :return: a bool object (True if cell should be selected)
    """
    if not is_markdown(cell):
        return False

    return cell.soup.select_one(css_selector) is not None


def is_new_slide(cell: Cell, subslide=True) -> bool:
    """
    Selects cells where a new slide/subslide starts
    :param cell: Cell object to select
    :param subslide: False if subslides should not be selected
    :return: a bool object (True if cell should be selected)
    """
    slide_types = {'slide'}
    if subslide:
        slide_types.add('subslide')
    return has_slide_type(cell, slide_types)


# -- Default Selectors --
DefaultSelector.register_selector('contains', contains)
DefaultSelector.register_selector('has_match', has_match)
DefaultSelector.register_selector('empty', is_empty)
DefaultSelector.register_selector('is_empty', is_empty)
DefaultSelector.register_selector('has_byte_size', has_byte_size)
DefaultSelector.register_selector('has_tag', has_tag)

# -- Code Specific Selectors --
DefaultSelector.register_selector('has_output', has_output)
DefaultSelector.register_selector('has_output_type', has_output_type)

# -- Markdown Specific Selectors --
DefaultSelector.register_selector('has_html_tag', with_css_selector)
DefaultSelector.register_selector('with_css_selector', with_css_selector)

# -- Cell Types --
DefaultSelector.register_selector('has_type', has_type)
DefaultSelector.register_selector('raw_cells', is_raw)
DefaultSelector.register_selector('is_raw', is_raw)
DefaultSelector.register_selector('markdown_cells', is_markdown)
DefaultSelector.register_selector('is_markdown', is_markdown)
DefaultSelector.register_selector('code_cells', is_code)
DefaultSelector.register_selector('is_code', is_code)

# -- Slide cells --
DefaultSelector.register_selector('has_slide_type', has_slide_type)
DefaultSelector.register_selector('is_new_slide', is_new_slide)
