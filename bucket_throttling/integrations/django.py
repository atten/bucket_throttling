from typing import Callable

from django.http.response import JsonResponse
from django.utils.translation import ugettext_lazy as _

from ..translation import localize_timedelta
from ..utils import *


class BucketThrottlingMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    @classmethod
    def process_view(cls, request, view_func, view_args, view_kwargs):
        if hasattr(view_func, 'throttling_rules'):
            rules = view_func.throttling_rules
            arguments_func = view_func.throttling_arguments_func
            options = view_func.throttling_options

            if isinstance(rules, ThrottlingRule):
                rules = [rules]
            if not arguments_func:
                arguments_func = cls.get_throttling_arguments

            arguments = arguments_func(request, view_func, view_args, view_kwargs)
            buckets = get_buckets(rules, arguments, options)
            timeout = check_throttle(buckets)

            if not timeout:
                commit_request(buckets)
                return
            else:
                return HttpResponseThrottled(timeout)

    @staticmethod
    def get_throttling_arguments(request, view_func, view_args, view_kwargs):
        """аргументы по умолчанию, от которых вычисляется ключ для корзины"""
        return {
            'user': request.user.id,
            'method': request.method,
            'view': view_func.__name__
        }


def throttle_request(throttling_rules: [RuleList, ThrottlingRule],
                     throttling_arguments_func: Callable=None,
                     throttling_options: ThrottlingOptions=None) -> Callable:
    """
    Декоратор для view-функций, подлежащих тротлингу.
    :param throttling_rules: Один экземпляр ThrottlingRule или список
    :param throttling_arguments_func: Функция, от которой вычисляется набор аргументов для корзины.
                                      Если не задана, берётся ф-ия по умолчанию.
    :param throttling_options: Экземпляр ThrottlingOptions, если нужны кастомные настройки.
    """
    def decorator(func):
        func.throttling_rules = throttling_rules
        func.throttling_arguments_func = throttling_arguments_func
        func.throttling_options = throttling_options
        return func
    return decorator


class HttpResponseThrottled(JsonResponse):
    status_code = 429
    default_detail = _('Request throttled.')
    extra_detail = _('Expected available in %s.')

    def __init__(self, interval=None):
        if not interval:
            content = self.default_detail
        elif isinstance(interval, timedelta):
            # без необходимости не отображаем микросекунды
            if int(interval.total_seconds()) > 0 and interval.microseconds > 0:
                interval -= timedelta(microseconds=interval.microseconds)
            content = self.extra_detail % localize_timedelta(interval)
        else:
            content = self.extra_detail % str(interval)

        super().__init__({'detail': content})
