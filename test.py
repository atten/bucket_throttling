import unittest
import time

from django_bucket_throttling import setup
from django_bucket_throttling.utils import *


def try_request(rules: list, request_arguments: dict, delay_after: float, expected_result: bool):
    buckets = get_buckets(rules, **request_arguments)
    timeout = check_throttle(buckets)
    if not timeout:
        commit_request(buckets)
    if not expected_result and not timeout:
        raise AssertionError('Must throttle, but passed')
    elif expected_result and timeout:
        raise AssertionError('Must pass, but throttled for %s' % str(timeout))
    time.sleep(delay_after)


class MultipleUserTest(unittest.TestCase):
    TEST_RULES = [
        ThrottlingRule(max_requests=1, interval=timedelta(seconds=1)),
        ThrottlingRule(max_requests=2, interval=timedelta(seconds=5)),
    ]

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)

    @staticmethod
    def user_test(user_id: int, rules):
        try_request(rules, dict(path='path1', user_id=user_id), 0.2, True)
        try_request(rules, dict(path='path1', user_id=user_id), 1, False)
        try_request(rules, dict(path='path1', user_id=user_id), 0.1, True)
        try_request(rules, dict(path='path1', user_id=user_id), 0.1, False)

        try_request(rules, dict(path='path2', user_id=user_id), 0.1, True)
        try_request(rules, dict(path='path2', user_id=user_id), 1, False)
        try_request(rules, dict(path='path2', user_id=user_id), 0.1, True)
        try_request(rules, dict(path='path2', user_id=user_id), 0.1, False)

    def test_users(self):
        setup(redis_port=6363, periods_to_overtake=0)
        self.user_test(1, self.TEST_RULES)
        self.user_test(2, self.TEST_RULES)


class BurstTest(unittest.TestCase):
    TEST_RULES = [
        ThrottlingRule(max_requests=30, interval=timedelta(seconds=3)),
    ]

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)

    @staticmethod
    def burst_test(user_id: int, rules):
        for i in range(15):
            try_request(rules, dict(path='path3', user_id=user_id), 0.01, True)
        time.sleep(3)
        for i in range(45):
            try_request(rules, dict(path='path3', user_id=user_id), 0.01, True)
        try_request(rules, dict(path='path3', user_id=user_id), 0.01, False)
        time.sleep(3)

    def test_burst(self):
        setup(redis_port=6363, periods_to_overtake=1)
        self.burst_test(1, self.TEST_RULES)
        self.burst_test(1, self.TEST_RULES)


if __name__ == "__main__":
    unittest.main()
