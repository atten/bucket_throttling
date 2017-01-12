from typing import List

from .models import ThrottlingBucket
from .settings import get_setting
from datetime import timedelta


BucketList = List[ThrottlingBucket]


def get_buckets(request) -> BucketList:
    """Возвращает вёдра, попадающие под правила для запроса"""
    ret = []
    for rule in get_setting('RULES', []):
        if rule.is_suitable(request):
            ret.append(ThrottlingBucket(rule, request))
    return ret


def get_timeout(buckets: BucketList) -> timedelta:
    """Возвращает интервал, который осталось подождать до опустошения вёдер"""
    ret = timedelta()
    for b in buckets:
        t = b.check_timeout()
        if t and t > ret:
            ret = t
    return ret


def commit_request(buckets: BucketList):
    """Уведомляет каждое ведро о том, что запрос исполнен"""
    [b.commit_request() for b in buckets]
