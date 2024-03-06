from nbmanips.cell.cell_output import CellOutput
from nbmanips.cell.cells import Cell, CodeCell, MarkdownCell, RawCell
from nbmanips.cell.output_parsers import HtmlParser, ImageParser, TextParser

CellOutput.register_parser("text", TextParser())
CellOutput.register_parser("text/html", HtmlParser())
CellOutput.register_parser("image", ImageParser())


__all__ = ["Cell", "CellOutput", "MarkdownCell", "CodeCell", "RawCell"]
