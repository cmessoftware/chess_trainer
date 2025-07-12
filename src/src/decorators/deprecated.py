import warnings
import functools


def deprecated(reason: str = ""):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = f"The function {func.__name__} is obsolete."
            if reason:
                msg += f" {reason}"
            warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator
