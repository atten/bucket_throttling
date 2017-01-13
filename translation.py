from django.utils.translation import ngettext
from datetime import timedelta


def localize_timedelta(delta: timedelta) -> str:
    ret = []
    num_years = int(delta.days / 365)
    if num_years > 0:
        delta -= timedelta(days=num_years * 365)
        ret.append(ngettext('%d year', '%d years', num_years) % num_years)

    if delta.days > 0:
        ret.append(ngettext('%d day', '%d days', delta.days) % delta.days)

    num_hours = int(delta.seconds / 3600)
    if num_hours > 0:
        delta -= timedelta(hours=num_hours)
        ret.append(ngettext('%d hour', '%d hours', num_hours) % num_hours)

    num_minutes = int(delta.seconds / 60)
    if num_minutes > 0:
        delta -= timedelta(minutes=num_minutes)
        ret.append(ngettext('%d minute', '%d minutes', num_minutes) % num_minutes)

    num_seconds = delta.seconds
    if num_seconds > 0:
        delta -= timedelta(seconds=num_seconds)
        ret.append(ngettext('%d second', '%d seconds', num_seconds) % num_seconds)

    num_miliseconds = int(delta.microseconds / 1000)
    if num_miliseconds > 0:
        ret.append(ngettext('%d ms', '%d ms', num_miliseconds) % num_miliseconds)

    if not len(ret):
        ret.append(ngettext('%d second', '%d seconds', 0) % 0)

    return ' '.join(ret)
