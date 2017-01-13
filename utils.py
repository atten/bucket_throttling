from typing import List

from . import ThrottlingBucket, ThrottlingRule
from datetime import timedelta


RuleList = List[ThrottlingRule]
BucketList = List[ThrottlingBucket]


def get_buckets(rules: RuleList, **arguments) -> BucketList:
    """
    Возвращает вёдра, созданные путём комбинации списка правил с аргументами запроса.
    """
    ret = []
    if not rules:
        return ret
    for rule in rules:
        ret.append(ThrottlingBucket(rule, **arguments))
    return ret


def check_throttle(buckets: BucketList) -> timedelta:
    """Возвращает интервал, который осталось подождать до истечения таймаута вёдер"""
    ret = timedelta()
    for b in buckets:
        t = b.check_throttle()
        if t and t > ret:
            ret = t
    return ret


def commit_request(buckets: BucketList):
    """Уведомляет каждое ведро о том, что запрос исполнен"""
    [b.commit_request() for b in buckets]
