from abc import ABCMeta, abstractmethod

from nbmanips.cell.cell_utils import COLOR_SUPPORTED

try:
    from html2text import html2text
except ImportError:
    html2text = None

try:
    from img2text import img_to_ascii
except ImportError:
    img_to_ascii = None


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
    def parse(
        self,
        content,
        width=80,
        colorful=COLOR_SUPPORTED,
        bright=COLOR_SUPPORTED,
        reverse=True,
        **kwargs,
    ):
        if callable(img_to_ascii):
            return img_to_ascii(
                content,
                base64=True,
                colorful=colorful,
                reverse=reverse,
                width=width,
                bright=bright,
                **kwargs,
            )
        else:
            raise ModuleNotFoundError(
                'You need to pip install img2text for readable option'
            )

    @property
    def default_state(self):
        return img_to_ascii is not None


class HtmlParser(ParserBase):
    def parse(self, content, width=78, **kwargs):
        if callable(html2text):
            return html2text(content, bodywidth=width, **kwargs)
        else:
            raise ModuleNotFoundError(
                'You need to pip install html2txt for readable option'
            )

    @property
    def default_state(self):
        return html2text is not None
