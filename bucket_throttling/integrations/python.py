from functools import wraps

from .. import ThrottlingOptions
from ..utils import get_buckets, check_throttle, commit_request, RuleList


def throttled(rules: RuleList, arguments_func=None, options: ThrottlingOptions=None):
    """
    Decorator for functions and methods. Once throttled, will skip evaluation and return None
    """
    if arguments_func is None:
        arguments_func = lambda *a, **kw: dict(args=a, **kw)

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            arguments_bundle = arguments_func(*args, **kwargs)
            buckets = get_buckets(rules, arguments_bundle, options)
            timeout = check_throttle(buckets)

            if not timeout:
                result = func(*args, **kwargs)
                commit_request(buckets)
                return result

        return wrapper
    return decorator
