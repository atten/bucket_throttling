from datetime import datetime, timedelta
from typing import Optional, Union

from django.core.cache import cache

from .translation import localize_timedelta


def build_cache_key(**arguments) -> str:
    parts = []
    for k, v in arguments.items():
        parts.append(k)
        parts.append(v)
    return ';'.join(map(lambda s: str(s).replace(' ', '_'), parts))


class ThrottlingRule:
    max_requests = None
    interval = None

    def __init__(self, max_requests: int, interval: 'timedelta'):
        self.max_requests = max_requests
        self.interval = interval

    def __str__(self):
        return 'ThrottlingRule: %d requests per %s' % (self.max_requests,
                                                       localize_timedelta(self.interval))

    @property
    def cache_key(self) -> str:
        return build_cache_key(requests=self.max_requests, per=self.interval)


class ThrottlingBucket:
    updated_at_key = None
    capacity_key = None
    cache_dict = None
    rule = None
    request = None

    def __init__(self, rule: ThrottlingRule, **arguments):
        base_key = rule.cache_key + build_cache_key(**arguments)
        self.rule = rule
        self.updated_at_key = base_key + ';updated_at'
        self.capacity_key = base_key + ';capacity'
        self.cache_dict = cache.get_many([self.updated_at_key, self.capacity_key])

    @property
    def _capacity(self) -> Union[None, int]:
        """Оставшаяся ёмкость ведра"""
        return self.cache_dict.get(self.capacity_key)

    @property
    def _updated_at(self) -> Union[None, timedelta]:
        """Время обновления ведра"""
        return self.cache_dict.get(self.updated_at_key)

    def check_throttle(self) -> Union[None, timedelta]:
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
        periods_to_overtake = 0
        cache_interval = self.rule.interval.total_seconds() * (periods_to_overtake + 1)
        updated_at = self._updated_at
        max_capacity = self.rule.max_requests - 1
        now = datetime.utcnow()

        if updated_at is None:
            # во избежание одновременного присвоения значения ёмкости из нескольких потоков,
            # мы сначала пробуем нарастить ёмкость ведра
            print('create', self.updated_at_key, 'for', cache_interval, '(%d capacity)' % max_capacity)
            if self._capacity is None or cache.incr(self.capacity_key, max_capacity) > max_capacity:
                cache.set(self.capacity_key, max_capacity, cache_interval)
            cache.set(self.updated_at_key, now, cache_interval)

        elif updated_at < now - self.rule.interval:
            print('update', self.updated_at_key, '(+%d)' % max_capacity)
            cache.set_many({
                self.capacity_key: (self._capacity or 0) + max_capacity,
                self.updated_at_key: now
            }, cache_interval)
        else:
            print('spent', self.updated_at_key, '%d remaining', self._capacity - 1)
            cache.decr(self.capacity_key)
