import re
from datetime import datetime, timedelta
from typing import Optional, Union

from django.core.cache import cache
from django.utils.functional import cached_property

from .translation import localize_timedelta


class ThrottlingRule:
    url_regex = None
    max_requests = None
    interval = None
    methods = None
    distinct_by_user = None

    def __init__(self, max_requests: int, interval: 'timedelta', methods: Optional[list]=None, url_path: Optional[str]=None, distinct_by_user: Optional[bool]=False):
        self.url_regex = re.compile(url_path) if url_path else None
        self.max_requests = max_requests
        self.interval = interval
        self.methods = list(methods or [])
        self.distinct_by_user = distinct_by_user

    def __str__(self):
        return 'ThrottlingRule: %d %s requests%s per %s' % (self.max_requests,
                                                            ','.join(self.methods),
                                                            ' ' + self.url_regex.pattern if self.url_regex is not None else '',
                                                            localize_timedelta(self.interval))

    def is_suitable(self, request) -> bool:
        """Подходит ли данное правило к проверке запроса"""
        return (self.url_regex is None or self.url_regex.match(request.path)) and\
               (not (self.distinct_by_user and request.user.is_anonymous)) and\
               (not self.methods or request.method in self.methods)


class ThrottlingBucket:
    updated_at_key = None
    capacity_key = None
    cache_dict = None
    rule = None
    request = None

    def __init__(self, rule: ThrottlingRule, request):
        self.rule = rule
        self.request = request
        self.updated_at_key = self._base_key + ';updated_at'
        self.capacity_key = self._base_key + ';capacity'
        self.cache_dict = cache.get_many([self.updated_at_key, self.capacity_key])

    @cached_property
    def _base_key(self) -> str:
        parts = []
        r = self.rule
        if r.url_regex:
            parts.append(r.url_regex.pattern)
        if r.methods:
            parts += ['methods'] + r.methods
        if r.distinct_by_user:
            parts += ['user', self.request.user.id]
        parts += [r.max_requests, r.interval]
        return ';'.join(map(lambda s: str(s).replace(' ', '_'), parts))

    @property
    def _capacity(self) -> Union[None, int]:
        """Оставшаяся ёмкость ведра"""
        return self.cache_dict.get(self.capacity_key)

    @property
    def _updated_at(self) -> Union[None, timedelta]:
        return self.cache_dict.get(self.updated_at_key)

    def check_timeout(self) -> Union[None, timedelta]:
        """
        Возвращает None, если лимит ведра не превышен,
        иначе интервал времени, через который ведро опустеет
        """
        updated_at = self._updated_at
        now = datetime.utcnow()
        if self._capacity == 0 and updated_at is not None and updated_at + self.rule.interval > now:
            return updated_at + self.rule.interval - now
        return None

    def commit_request(self):
        """
        Если в кэше ведра нет, создаём его с текущим timestamp и ёмкостью, меньшей максимальной на 1
        Если ведро обновлялось раньше, чем истёк его интервал действия, наращиваем его ёмкость и обновляем дату обновления
        Если ведро актуально, уменьшаем его ёмкость на 1
        """
        # Мы предполагаем, что пользователь не злоумышленник, поэтому даём ему возможность совершать больше
        # реквестов в отведённый интервал, если у ведра осталась неиспользованная емкость.
        # Сделав таймаут кэша равным нескольким интервалам действия ведра, мы
        # ограничим возможность наверстать его неиспользованную ёмкость.
        cache_interval = self.rule.interval.total_seconds() * 2
        updated_at = self._updated_at
        max_capacity = self.rule.max_requests - 1
        now = datetime.utcnow()

        if updated_at is None:
            # во избежание одновременного присвоения значения ёмкости из нескольких потоков,
            # мы сначала пробуем нарастить ёмкость ведра
            # print('create', self.updated_at_key)
            if self._capacity is None or cache.incr(self.capacity_key, max_capacity) > max_capacity:
                cache.set(self.capacity_key, max_capacity, cache_interval)
            cache.set(self.updated_at_key, now, cache_interval)

        elif updated_at < now - self.rule.interval:
            # print('update', self.updated_at_key)
            cache.set_many({
                self.capacity_key: (self._capacity or 0) + max_capacity,
                self.updated_at_key: now
            }, cache_interval)
        else:
            # print('spent', self.updated_at_key)
            cache.decr(self.capacity_key)
