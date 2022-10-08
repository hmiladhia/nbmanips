from functools import wraps


def partial(func, *args, **keywords):
    @wraps(func)
    def new_func(*f_args, **f_keywords):
        new_keywords = {**f_keywords, **keywords}
        return func(*f_args, *args, **new_keywords)

    return new_func
