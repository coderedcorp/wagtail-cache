"""
Registers wagtail-cache in the wagtail admin dashboard.
"""
from django.urls import include
from django.urls import path
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from wagtailcache import urls


class CacheMenuItem(MenuItem):
    """
    Registers wagtail-cache in wagtail admin for superusers.
    """

    def is_shown(self, request):
        return request.user.is_superuser


@hooks.register("register_admin_urls")
def register_admin_urls():
    """
    Registers wagtail-cache urls in the wagtail admin.
    """
    return [
        path(
            "cache/",
            include((urls, "wagtailcache"), namespace="wagtailcache_admin"),
        ),
    ]


@hooks.register("register_settings_menu_item")
def register_cache_menu():
    """
    Registers wagtail-cache settings panel in the wagtail admin.
    """
    return CacheMenuItem(
        _("Cache"),
        reverse("wagtailcache_admin:index"),
        icon_name="wagtailcache-bolt",
    )


@hooks.register("register_icons")
def register_icons(icons):
    """
    Add custom SVG icons to the Wagtail admin.
    """
    # These SVG files should be in the django templates folder, and follow exact
    # specifications to work with Wagtail:
    # https://github.com/wagtail/wagtail/pull/6028
    icons.append("wagtailcache/wagtailcache-bolt.svg")
    return icons
