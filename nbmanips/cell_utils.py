import shutil
from abc import ABCMeta, abstractmethod
from textwrap import wrap

from nbmanips.color import supports_color

try:
    import pygments
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import TerminalFormatter
except ImportError:
    pygments = None
    get_lexer_by_name = None
    TerminalFormatter = object

try:
    import colorama

    colorama.init()
except ImportError:
    colorama = None

try:
    from html2text import html2text
except ImportError:
    html2text = None

try:
    from img2text import img_to_ascii
except ImportError:
    img_to_ascii = None

styles = {"single": "││┌─┐└─┘",
          "double": "║║╔═╗╚═╝",
          "grid": '||+-++-+',
          "separated": '||+=++=+',
          "rounded": "||.-.'-'",
          "dots": "::......",
          "simple": '  ======',
          }

COLOR_SUPPORTED = supports_color()
PYGMENTS_SUPPORTED = COLOR_SUPPORTED and pygments is not None


def printable_cell(text, width=None, style='single', color=None, pygments_lexer=None):
    width = width or (shutil.get_terminal_size().columns - 1)
    style_l, style_r, style_ul, style_u, style_ur, style_dl, style_d, style_dr = styles[style]

    color_start, color_end = "", ""
    if color:
        color = 'WHITE' if color is None else color.upper()
        color_start, color_end = (vars(colorama.Fore)[color.upper()], colorama.Fore.RESET)

    text_width = width - 2 - len(style_l) - len(style_r)

    code_lines = []
    for code_line in text.split('\n'):
        code_lines.extend(wrap(code_line, text_width, tabsize=4))
    diff = [text_width - len(code_line) for code_line in code_lines]

    code = '\n'.join(code_lines)
    if pygments_lexer:
        if pygments is None:
            raise ModuleNotFoundError("You need to install pygments first.\n pip install nbmanips[pygments]")

        formatter = TerminalFormatter()
        lexer = get_lexer_by_name(pygments_lexer)
        code_lines = pygments.highlight(code, lexer, formatter)[:-1].split('\n')

    result = [color_start + style_ul + style_u * (width - len(style_ul) - len(style_ur)) + style_ur + color_end]
    result.extend([
        f"{color_start}{style_l}{color_end}"
        f" {line}{' ' * d} "
        f"{color_start}{style_r}{color_end}"
        for line, d in zip(code_lines, diff)
    ])
    result.append(color_start + style_dl + style_d * (width - len(style_dl) - len(style_dr)) + style_dr + color_end)
    return '\n'.join(result)


class ParserBase(metaclass=ABCMeta):
    @abstractmethod
    def parse(self, content, **kwargs):
        return content

    @property
    def default_state(self):
        return True


class TextParser(ParserBase):
    def parse(self, content, **kwargs):
        return content


class ImageParser(ParserBase):
    def parse(self, content, width=80, colorful=COLOR_SUPPORTED, bright=COLOR_SUPPORTED, reverse=True, **kwargs):
        if callable(img_to_ascii):
            return img_to_ascii(content, base64=True, colorful=colorful, reverse=reverse,
                                width=width, bright=bright, **kwargs)
        else:
            raise ModuleNotFoundError('You need to pip install img2text for readable option')

    @property
    def default_state(self):
        return img_to_ascii is not None


class HtmlParser(ParserBase):
    def parse(self, content, width=78, **kwargs):
        if callable(html2text):
            return html2text(content,  bodywidth=width, **kwargs)
        else:
            raise ModuleNotFoundError('You need to pip install html2txt for readable option')

    @property
    def default_state(self):
        return html2text is not None
