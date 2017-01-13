from .utils import *
from .response import HttpResponseThrottled


class ThrottledViewSetMixIn:
    """Позволяет применять правила троттлинга к отдельным действиям для ViewSet'а (create, delete, custom_action...)"""

    bucket_throttle_rules = None     # можно передавать словарь {action: [rule1, rule2...]}

    def dispatch(self, request, *args, **kwargs):
        action = self.action_map.get(request.method.lower())
        rules = self.bucket_throttle_rules.get(action)
        if rules:
            buckets = get_buckets(request, rules)
            timeout = get_timeout(buckets)
            if timeout:
                return HttpResponseThrottled(timeout)
            else:
                commit_request(buckets)
        return super().dispatch(request, *args, **kwargs)
