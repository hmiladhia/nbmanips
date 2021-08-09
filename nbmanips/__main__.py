import sys
from nbmanips import Notebook


def main():
    if sys.argv[1] == 'show':
        nb = Notebook.read_ipynb(sys.argv[2])
        if len(sys.argv) >= 3:
            nb = nb.select(*sys.argv[3:])
        nb.show()
    else:
        ...


if __name__ == '__main__':
    main()
