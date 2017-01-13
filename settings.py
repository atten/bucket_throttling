from django.conf import settings
from datetime import timedelta
from .models import ThrottlingRule

DJANGO_BUCKET_THROTTLING = {
    'RULES': [
        # ThrottlingRule(max_requests=2, interval=timedelta(seconds=10), methods=['POST'], distinct_by_user=True),
    ],
}


def get_setting(name, default=None):
    """Берем значение опции из глобальных настроек, если есть, иначе берем из локальных"""
    if hasattr(settings, 'DJANGO_BUCKET_THROTTLING') and name in settings.DJANGO_BUCKET_THROTTLING:
        return settings.DJANGO_BUCKET_THROTTLING[name]
    return DJANGO_BUCKET_THROTTLING.get(name, default)
