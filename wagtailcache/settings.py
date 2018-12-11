"""
Default django settings for wagtail-cache.
"""

from django.conf import settings
from django.utils.lru_cache import lru_cache

DEFAULTS = {
    'WAGTAIL_CACHE': True,
    'WAGTAIL_CACHE_BACKEND': 'default',
    'WAGTAIL_CACHE_HEADER': 'X-Wagtail-Cache',
}

@lru_cache()
def get_config():
    """
    Gets settings from django settings file or defaults.
    """
    config = DEFAULTS.copy()
    for var in config:
        if hasattr(settings, var):
            config[var] = getattr(settings, var)
    return config

wagtailcache_settings = get_config()
