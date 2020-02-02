from typing import Optional
from django import template
from django.core.cache import caches
from django.utils.translation import gettext_lazy as _
from wagtailcache.settings import wagtailcache_settings


register = template.Library()


def seconds_to_readable(seconds: int) -> str:
    """
    Converts int seconds to a human readable string.
    """
    if seconds <= 0:
        return '{0} {1}'.format(str(seconds), _('seconds'))

    mins, secs = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    days, hrs = divmod(hrs, 24)
    pretty_time = ''
    if days > 0:
        pretty_time += ' {0} {1}'.format(str(days), _('days') if days > 1 else _('day'))
    if hrs > 0:
        pretty_time += ' {0} {1}'.format(str(hrs), _('hours') if hrs > 1 else _('hour'))
    if mins > 0:
        pretty_time += ' {0} {1}'.format(str(mins), _('minutes') if mins > 1 else _('minute'))
    if secs > 0:
        pretty_time += ' {0} {1}'.format(str(secs), _('seconds') if secs > 1 else _('second'))
    return pretty_time


@register.filter
def get_wagtailcache_setting(value: str) -> Optional[object]:
    return getattr(wagtailcache_settings, value, None)


@register.simple_tag
def cache_timeout() -> str:
    timeout = caches[wagtailcache_settings.WAGTAIL_CACHE_BACKEND].default_timeout
    return seconds_to_readable(timeout)
