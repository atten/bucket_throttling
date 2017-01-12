from datetime import timedelta

from django.http.response import JsonResponse
from django.utils.translation import ugettext_lazy as _

from .translation import localize_timedelta


class HttpResponseThrottled(JsonResponse):
    status_code = 429
    default_detail = _('Request was throttled.')
    extra_detail = _('Expected available in %s.')

    def __init__(self, interval=None):
        if not interval:
            content = self.default_detail
        elif isinstance(interval, timedelta):
            content = self.extra_detail % localize_timedelta(interval)
        else:
            content = self.extra_detail % str(interval)

        super().__init__({'detail': content})
