from .utils import *
from .response import HttpResponseThrottled


class BucketThrottlingMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        buckets = get_buckets(request)
        timeout = get_timeout(buckets)

        if not timeout:
            response = self.get_response(request)
            commit_request(buckets)
        else:
            response = HttpResponseThrottled(timeout)
        return response
