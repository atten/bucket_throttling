from django.http.response import JsonResponse
from django.utils.translation import ugettext_lazy as _

from ..translation import localize_timedelta
from ..utils import *


class BucketThrottlingMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        buckets = get_buckets(request)
        timeout = check_throttle(buckets)

        if not timeout:
            commit_request(buckets)
            response = self.get_response(request)
        else:
            response = HttpResponseThrottled(timeout)
        return response


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
