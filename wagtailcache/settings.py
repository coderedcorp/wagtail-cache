"""
Default django settings for wagtail-cache.
"""

from typing import Text
from django.conf import settings


class _DefaultSettings:

    WAGTAIL_CACHE = True
    WAGTAIL_CACHE_BACKEND = "default"
    WAGTAIL_CACHE_HEADER = "X-Wagtail-Cache"

    def __getattribute__(self, attr: Text):
        return getattr(settings, attr, super().__getattribute__(attr))


wagtailcache_settings = _DefaultSettings()
