from time import perf_counter
from functools import wraps

from .colorize import Msg

def timer(func):
    def inner(*args, **kwargs):
        from time import perf_counter
        start = perf_counter()
        result = func(*args, **kwargs)
        v = perf_counter() - start
        Msg.Dim(f'{func.__name__} > ELAPSED {v:.5f} Sec.')
        return result
    return inner