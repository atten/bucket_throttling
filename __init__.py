from datetime import datetime, timedelta
from typing import Optional, Union

import redis as r

from .translation import localize_timedelta


def setup(redis_port=6379, periods_to_overtake=0):
    global REDIS_INSTANCE, PERIODS_TO_OVERTAKE
    REDIS_INSTANCE = r.StrictRedis(port=redis_port)
    PERIODS_TO_OVERTAKE = periods_to_overtake


def redis_instance():
    global REDIS_INSTANCE
    return REDIS_INSTANCE


def build_cache_key(**arguments) -> str:
    parts = []
    for k in sorted(arguments):
        parts.append(k)
        parts.append(arguments[k])
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
    updated_at_key = 'updated_at'
    capacity_key = 'capacity'
    base_key = None
    cache_dict = None
    rule = None
    request = None
    redis = None

    def __init__(self, rule: ThrottlingRule, **arguments):
        self.redis = redis_instance()
        self.base_key = 'THROTTLING:' + rule.cache_key + build_cache_key(**arguments)
        self.rule = rule
        self.cache_dict = {k.decode(): v for (k, v) in self.redis.hgetall(self.base_key).items()}

    @property
    def _capacity(self) -> Union[None, int]:
        """Оставшаяся ёмкость ведра"""
        d = self.cache_dict.get(self.capacity_key)
        return int(d) if d is not None else d

    @property
    def _updated_at(self) -> Union[None, timedelta]:
        """Время обновления ведра"""
        d = self.cache_dict.get(self.updated_at_key)
        return datetime.fromtimestamp(float(d)) if d is not None else d

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
        global PERIODS_TO_OVERTAKE
        cache_interval = self.rule.interval.total_seconds() * (PERIODS_TO_OVERTAKE + 1)
        cache_interval = max(int(cache_interval), 1)
        updated_at = self._updated_at
        max_capacity = self.rule.max_requests - 1
        now = datetime.utcnow()

        if updated_at is None:
            # во избежание одновременного присвоения значения ёмкости из нескольких потоков,
            # мы сначала пробуем нарастить ёмкость ведра
            print('create', self.base_key, 'for', cache_interval, '(%d capacity)' % max_capacity)
            if self._capacity is None or self.redis.hincrby(self.base_key, self.updated_at_key, 1) > max_capacity:
                self.redis.hset(self.base_key, self.capacity_key, max_capacity)
                self.redis.expire(self.base_key, cache_interval)
            self.redis.hset(self.base_key, self.updated_at_key, now.timestamp())

        elif updated_at < now - self.rule.interval:
            print('update', self.base_key, '(+%d)' % max_capacity)
            self.redis.hmset(self.base_key, {
                self.capacity_key: (self._capacity or 0) + max_capacity,
                self.updated_at_key: now.timestamp()
            })
            self.redis.expire(self.base_key, cache_interval)
        else:
            print('spent', self.base_key, '%d remaining', self._capacity - 1)
            self.redis.hincrby(self.base_key, self.capacity_key, -1)
