from typing import List

from .models import ThrottlingBucket
from .settings import get_setting
from datetime import timedelta


BucketList = List[ThrottlingBucket]


def get_buckets(request, rules=None) -> BucketList:
    """
    Возвращает вёдра, попадающие под правила для запроса.
    Если правила не указаны, берём их из настроек.
    """
    ret = []
    if rules is None:
        rules = get_setting('RULES', [])

    for rule in rules:
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
