import re
import shutil
from mimetypes import guess_type
from textwrap import wrap
from typing import Union

from nbmanips.cell.color import supports_color

try:
    import pygments
    from pygments.formatters import TerminalFormatter

    FORMATTER = TerminalFormatter()
except ImportError:
    pygments = None
    TerminalFormatter = None
    FORMATTER = None

try:
    import colorama

    colorama.init()
except ImportError:
    colorama = None


styles = {
    'single': '││┌─┐└─┘',
    'double': '║║╔═╗╚═╝',
    'grid': '||+-++-+',
    'separated': '||+=++=+',
    'rounded': "||.-.'-'",
    'dots': '::......',
    'simple': '  ======',
    'copy': ('', '', '#', '-', '-', '', '', ''),
}

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
COLOR_SUPPORTED = supports_color()
PYGMENTS_SUPPORTED = COLOR_SUPPORTED and pygments is not None


def printable_cell(text, width=None, style='single', color=None, pygments_lexer=None):
    width = width or (shutil.get_terminal_size().columns - 1)
    style_l, style_r, style_ul, style_u, style_ur, style_dl, style_d, style_dr = styles[
        style
    ]
    space_l = ' ' if style_l else ''
    space_r = ' ' if style_r else ''

    color_start, color_end = '', ''
    if color:
        color = 'WHITE' if color is None else color.upper()
        color_start, color_end = (
            vars(colorama.Fore)[color.upper()],
            colorama.Fore.RESET,
        )

    text_width = width - len(space_l) - len(space_r) - len(style_l) - len(style_r)

    code_lines = []
    for code_line in text.split('\n'):
        code_lines.extend(wrap(code_line, text_width, tabsize=4))
    diff = [text_width - len(code_line) for code_line in code_lines]

    code = '\n'.join(code_lines)
    if pygments_lexer:
        code_lines = pygments.highlight(code, pygments_lexer, FORMATTER)[:-1].split(
            '\n'
        )

    result = [
        color_start
        + style_ul
        + style_u * (width - len(style_ul) - len(style_ur))
        + style_ur
        + color_end
    ]
    result.extend(
        [
            f'{color_start}{style_l}{color_end}'
            + space_l
            + f"{line}{' ' * d}"
            + space_r
            + f'{color_start}{style_r}{color_end}'
            for line, d in zip(code_lines, diff)
        ]
    )
    result.append(
        color_start
        + style_dl
        + style_d * (width - len(style_dl) - len(style_dr))
        + style_dr
        + color_end
    )
    return '\n'.join(line.rstrip(' ') for line in result)


def monochrome(text):
    """
    Source:
    https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python

    :param text: any text
    """
    return ANSI_ESCAPE.sub('', text)


def get_mime_type(path):
    return guess_type(path)[0]


def _get_output_types(output_type: Union[set, dict, str]) -> set:
    if isinstance(output_type, str):
        if '/' in output_type:
            return {output_type, output_type.split('/')[0]}
        return {output_type}

    output_types = set()
    for output in output_type:
        output_types |= _get_output_types(output)
    return output_types


def _to_html(text):
    import html

    return html.escape(text).encode('ascii', 'xmlcharrefreplace').decode('ascii')
