import sys
from nbmanips import *


def main():
    if sys.argv[1] == 'show':
        nb = Notebook.read_ipynb(sys.argv[2])

        for i, cell in enumerate(nb.cells):
            print(Cell(cell, i))
    else:
        ...


if __name__ == '__main__':
    main()
