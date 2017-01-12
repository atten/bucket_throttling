from django.utils.translation import ngettext as ng
from datetime import timedelta


def localize_timedelta(delta: timedelta) -> str:
    ret = []
    num_years = int(delta.days / 365)
    if num_years > 0:
        delta -= timedelta(days=num_years * 365)
        ret.append(ng('%d year', '%d years', num_years) % num_years)

    if delta.days > 0:
        ret.append(ng('%d day', '%d days', delta.days) % delta.days)

    num_hours = int(delta.seconds / 3600)
    if num_hours > 0:
        delta -= timedelta(hours=num_hours)
        ret.append(ng('%d hour', '%d hours', num_hours) % num_hours)

    num_minutes = int(delta.seconds / 60)
    if num_minutes > 0:
        delta -= timedelta(minutes=num_minutes)
        ret.append(ng('%d minute', '%d minutes', num_minutes) % num_minutes)

    num_seconds = delta.seconds
    if num_seconds > 0:
        delta -= timedelta(seconds=num_seconds)
        ret.append(ng('%d second', '%d seconds', num_seconds) % num_seconds)

    num_miliseconds = int(delta.microseconds / 1000)
    if num_miliseconds > 0:
        ret.append(ng('%d ms', '%d ms', num_miliseconds) % num_miliseconds)

    return ' '.join(ret)
