from typing import Union
import time

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.base_user import AbstractBaseUser
from django.conf import settings
from django.http.request import HttpRequest
from django.core.cache import cache
from django.test import SimpleTestCase
from django.test.runner import DiscoverRunner

from django_bucket_throttling.models import ThrottlingRule
from django_bucket_throttling.utils import *
from django_bucket_throttling.translation import localize_timedelta


UserType = Union[AnonymousUser, AbstractBaseUser]


TEST_SETTINGS = {
    'RULES': [
        ThrottlingRule('', max_requests=2, interval=timedelta(seconds=5), methods=['POST', 'PATCH', 'PUT', 'DELETE'], distinct_by_user=True),
        ThrottlingRule('path1', max_requests=1, interval=timedelta(seconds=1), methods=['GET'], distinct_by_user=True),
        ThrottlingRule('path2', max_requests=20, interval=timedelta(seconds=4), methods=['GET'], distinct_by_user=False),
    ]
}


class TestRequest(HttpRequest):
    def __init__(self, path, method, user):
        super().__init__()
        self.path = path
        self.method = method
        self.user = user


def create_user(**kwargs) -> AbstractBaseUser:
    ret = AbstractBaseUser()
    [setattr(ret, k, v) for k, v in kwargs.items()]
    return ret


def try_request(path: str, method: str, user: UserType, delay_after: float, expected_result: bool):
    print('%s %s [%s]' % (method, path, user.id or user))
    request = TestRequest(path, method, user)
    buckets = get_buckets(request)
    timeout = get_timeout(buckets)
    if not timeout:
        commit_request(buckets)
    if not expected_result and not timeout:
        raise AssertionError('Must throttle, but passed')
    elif expected_result and timeout:
        raise AssertionError('Must pass, but throttled for %s' % localize_timedelta(timeout))
    time.sleep(delay_after)


def anonymous_test():
    anonymous = AnonymousUser()
    try_request('path1', 'GET', anonymous, 0.1, True)
    try_request('path1', 'POST', anonymous, 0.1, True)
    try_request('path1', 'PATCH', anonymous, 0.1, True)
    try_request('path2', 'PUT', anonymous, 0.1, True)
    try_request('path2', 'DELETE', anonymous, 0.1, True)


def user_test(pk: int):
    user1 = create_user(id=pk)
    try_request('path1', 'GET', user1, 0.5, True)
    try_request('path1', 'POST', user1, 0.5, True)
    try_request('path1', 'PATCH', user1, 0.5, True)
    try_request('path2', 'PUT', user1, 0.5, False)
    try_request('path2', 'DELETE', user1, 0.5, False)


def burst_test():
    user1 = create_user(id=1)
    for i in range(10):
        try_request('path2', 'GET', user1, 0.01, True)
    time.sleep(4)
    for i in range(30):
        try_request('path2', 'GET', user1, 0.001, True)
    try_request('path2', 'GET', user1, 0.001, False)
    time.sleep(4)


class FunctionalTest(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        settings.DJANGO_BUCKET_THROTTLING = TEST_SETTINGS
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        cache.clear()
        super().tearDownClass()

    def test_all(self):
        anonymous_test()
        user_test(1)
        user_test(2)
        burst_test()
        burst_test()


class NoDbTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        pass

    def teardown_databases(self, old_config, **kwargs):
        pass
