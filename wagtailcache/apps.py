from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailCacheAppConfig(AppConfig):
    name = "wagtailcache"
    label = "wagtailcache"
    verbose_name = _("Wagtail Cache")
