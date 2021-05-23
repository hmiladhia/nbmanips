import shutil
from textwrap import wrap

from nbmanips.color import supports_color

try:
    import colorama

    colorama.init()
except ImportError:
    colorama = None


styles = {"single": "││┌─┐└─┘",
          "double": "║║╔═╗╚═╝",
          "grid": '||+-++-+',
          "separated": '||+=++=+',
          "rounded": "||.-.'-'",
          "dots": "::......",
          "simple": '  ======',
          }


def parse_style(style):
    l, r, ul, u, ur, dl, d, dr = style

    return l, r, ul, u, ur, dl, d, dr


def printable_cell(text, width=None, style='single', color=None):
    width = width or (shutil.get_terminal_size().columns - 1)
    style_l, style_r, style_ul, style_u, style_ur, style_dl, style_d, style_dr = parse_style(styles[style])

    color_start, color_end = "", ""
    if supports_color() and color:
        color_start, color_end = (vars(colorama.Fore)[color], colorama.Fore.ENDC)

    text_width = width - 2 - len(style_l) - len(style_r)

    result_list = []
    for text_line in text.split('\n'):
        result_list.extend(wrap(text_line, text_width, tabsize=4))

    result = [color_start + style_ul + style_u * (width - len(style_ul) - len(style_ur)) + style_ur + color_end]
    result.extend([f"{color_start}{style_l}{color_end} {line.ljust(text_width)} {color_start}{style_r}{color_end}" for line in result_list])
    result.append(color_start + style_dl + style_d * (width - len(style_dl) - len(style_dr)) + style_dr + color_end)
    return '\n'.join(result)
