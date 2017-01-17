from ..utils import *
from .django import HttpResponseThrottled


class ThrottledViewSetMixIn:
    """
    Позволяет применять правила троттлинга перед выполнением запросов.
    В пользовательских классах можно задавать правила в throttling_rules
    и аргументы для создания корзины, возвращаемые в get_throttling_arguments()
    """
    throttling_rules = None

    def dispatch(self, request, *args, **kwargs):
        buckets = self.get_throttling_buckets(request)
        if buckets:
            timeout = check_throttle(buckets)
            if timeout:
                return HttpResponseThrottled(timeout)
            else:
                commit_request(buckets)
        return super().dispatch(request, *args, **kwargs)

    def get_throttling_buckets(self, request):
        return get_buckets(self.get_throttling_rules(request), self.get_throttling_arguments(request))

    def get_throttling_rules(self, request):
        return self.throttling_rules

    def get_throttling_arguments(self, request):
        """аргументы по умолчанию, от которых вычисляется ключ для корзины"""
        return {
            'user': request.user.id,
            'action': self.action_map.get(request.method.lower()),
            'view': self.__class__.__name__
        }
