import sys
from nbmanips import Notebook


def main():
    if sys.argv[1] == 'show':
        nb = Notebook.read_ipynb(sys.argv[2])

        nb.show(*sys.argv[3:])
    else:
        ...


if __name__ == '__main__':
    main()
