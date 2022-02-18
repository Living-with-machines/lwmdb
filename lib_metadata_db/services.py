import functools

from django.db import connections


def reconnect(db_name):
    def decorator_reconnect(func):
        @functools.wraps(func)
        def wrapper_reconnect(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except Exception:
                db_connection = connections[db_name]
                db_connection.connect()
                result = func(*args, **kwargs)
            finally:
                return result

        return wrapper_reconnect

    return decorator_reconnect
