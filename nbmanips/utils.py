import os
import json

from collections import deque
from functools import wraps
from itertools import chain
from sys import getsizeof


def total_size(o, handlers=None):
    """
    Copyright 2012 Raymond Hettinger Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in the Software without restriction,
    including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the
    following conditions: The above copyright notice and this permission notice shall be included in all copies or
    substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NON INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    Returns the approximate memory footprint an object and all
    of its contents. Automatically finds the contents of the following builtin containers and their subclasses:
    tuple, list, deque, dict, set and frozenset. To search other containers, add handlers to iterate over their
    contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    """
    handlers = handlers or {}
    all_handlers = {tuple: iter,
                    list: iter,
                    deque: iter,
                    dict: lambda d: chain.from_iterable(d.items()),
                    set: iter,
                    frozenset: iter}
    all_handlers.update(handlers)     # user handlers take precedence
    seen = set()                      # track which object id's have already been seen
    default_size = getsizeof(0)       # estimate sizeof object without __sizeof__

    def sizeof(obj):
        if id(obj) in seen:       # do not double count the same object
            return 0
        seen.add(id(obj))
        s = getsizeof(obj, default_size)

        for typ, handler in all_handlers.items():
            if isinstance(obj, typ):
                s += sum(map(sizeof, handler(obj)))
                break
        return s

    return sizeof(o)


def get_ipynb_name(path) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def read_ipynb(notebook_path, encoding='utf-8'):
    with open(notebook_path, 'r', encoding=encoding) as f:
        return json.load(f)


def write_ipynb(notebook, notebook_path, encoding='utf-8'):
    with open(notebook_path, 'w', encoding=encoding) as f:
        json.dump(notebook, f)


def partial(func, *args, **keywords):
    @wraps(func)
    def new_func(*f_args, **f_keywords):
        new_keywords = {**f_keywords, **keywords}
        return func(*f_args, *args, **new_keywords)
    return new_func
