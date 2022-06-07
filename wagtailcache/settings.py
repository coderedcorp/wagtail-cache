"""
Default django settings for wagtail-cache.
"""

from typing import Text
from django.conf import settings


class _DefaultSettings:

    WAGTAIL_CACHE = True
    WAGTAIL_CACHE_BACKEND = "default"
    WAGTAIL_CACHE_HEADER = "X-Wagtail-Cache"
    WAGTAIL_CACHE_IGNORE_QS = [
        r"^_bta_.*$",  # Bronto
        r"^_ga$",  # Google Analytics
        r"^affiliate$",  # Instagram affiliates
        r"^ck_subscriber_id$",  # Instagram affiliates
        r"^dm_i$",  # Dotdigital
        r"^ef_.*$",  # Adobe Analytics
        r"^epik$",  # Pinterest
        r"^fb_source$",  # Facebook
        r"^fbclid$",  # Facebook
        r"^gclid$",  # Google AdWords
        r"^gclsrc$",  # Google DoubleClick
        r"^hsa_.*$",  # Hubspot
        r"^matomo_.*$",  # Matomo
        r"^mc_.*$",  # Mailchimp
        r"^msclkid$",  # Microsoft Advertising
        r"^mtm_.*$",  # Matomo
        r"^s_kwcid$",  # Adobe Analytics
        r"^trk_.*$",  # Listrak
        r"^utm_.*$",  # Google Analytics
    ]

    def __getattribute__(self, attr: Text):
        return getattr(settings, attr, super().__getattribute__(attr))


wagtailcache_settings = _DefaultSettings()
