from rest_framework.exceptions import Throttled

from ..utils import *
from .django import HttpResponseThrottled
from ..translation import localize_timedelta


class ThrottledViewSetMixIn:
    """
    Позволяет применять правила троттлинга перед выполнением запросов.
    В пользовательских классах можно задавать правила в throttling_rules
    и аргументы для создания корзины, возвращаемые в get_throttling_arguments()
    """
    throttling_rules = None
    throttling_distinct_kwargs = False

    def initial(self, request, *args, **kwargs):
        """
        Используем этот метод для обработки событий троттлинга, который вызывается в dispatch()
        непосредственно перед вызовом view-функции. Делаем это потому, что после вызова super().initial
        мы будем иметь пропатченный drf request и все нужные аттрибуты ViewSet'а
        """
        super().initial(request, *args, **kwargs)
        buckets = self.get_throttling_buckets(request)
        if buckets:
            timeout = check_throttle(buckets)
            if timeout:
                raise ThrottledException(timeout)
            commit_request(buckets)

    def get_throttling_buckets(self, request):
        return get_buckets(self.get_throttling_rules(request), self.get_throttling_arguments(request))

    def get_throttling_rules(self, request):
        return self.throttling_rules

    def get_throttling_arguments(self, request):
        """аргументы по умолчанию, от которых вычисляется ключ для корзины"""
        d = {
            'user': request.user.id,
            'action': self.action,
            'view': self.__class__.__name__
        }
        if self.throttling_distinct_kwargs:
            d.update(self.kwargs)
        return d


class ThrottledException(Throttled):
    def __init__(self, interval=None):
        if not interval:
            detail = HttpResponseThrottled.default_detail
        elif isinstance(interval, timedelta):
            # без необходимости не отображаем микросекунды
            if int(interval.total_seconds()) > 0 and interval.microseconds > 0:
                interval -= timedelta(microseconds=interval.microseconds)
            detail = HttpResponseThrottled.extra_detail % localize_timedelta(interval)
        else:
            detail = HttpResponseThrottled.extra_detail % str(interval)
        super().__init__(detail=detail)
