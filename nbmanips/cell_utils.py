import shutil
from textwrap import wrap

from nbmanips.color import supports_color

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


def parse_style(style):
    l, r, ul, u, ur, dl, d, dr = style

    return l, r, ul, u, ur, dl, d, dr


def printable_cell(text, width=None, style='single', color=None):
    width = width or (shutil.get_terminal_size().columns - 1)
    style_l, style_r, style_ul, style_u, style_ur, style_dl, style_d, style_dr = parse_style(styles[style])

    color_start, color_end = "", ""
    if color:
        color = 'BLACK' if color is None else color.upper()
        color_start, color_end = (vars(colorama.Fore)[color], colorama.Fore.RESET)

    text_width = width - 2 - len(style_l) - len(style_r)

    result_list = []
    for text_line in text.split('\n'):
        result_list.extend(wrap(text_line, text_width, tabsize=4))

    result = [color_start + style_ul + style_u * (width - len(style_ul) - len(style_ur)) + style_ur + color_end]
    result.extend([f"{color_start}{style_l}{color_end} {line.ljust(text_width)} {color_start}{style_r}{color_end}"
                   for line in result_list])
    result.append(color_start + style_dl + style_d * (width - len(style_dl) - len(style_dr)) + style_dr + color_end)
    return '\n'.join(result)


def get_readable(text, data_type, width=80, reverse=True, **kwargs):
    if data_type == 'text/html':
        if callable(html2text):
            return html2text(text)
        else:
            raise ModuleNotFoundError('You need to pip install html2txt for readable option')

    if data_type == 'image/png':
        if callable(img_to_ascii):
            colorful = kwargs.pop('colorful', COLOR_SUPPORTED)
            bright = kwargs.pop('bright', COLOR_SUPPORTED)
            return img_to_ascii(text, base64=True, colorful=colorful, reverse=reverse,
                                width=width, bright=bright, **kwargs)
        else:
            raise ModuleNotFoundError('You need to pip install img2text for readable option')

    return text
