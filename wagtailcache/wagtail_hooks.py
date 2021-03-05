"""
Registers wagtail-cache in the wagtail admin dashboard.
"""

from django.urls import include, path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail.admin.menu import MenuItem
from wagtail.core import hooks

from wagtailcache import urls
from wagtailcache.cache import clear_cache
from wagtailcache.icon import CACHE_ICON


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
        classnames="icon icon-" + CACHE_ICON,
    )


@hooks.register('after_create_page')
@hooks.register('after_edit_page')
def clear_wagtailcache(request, page):
    clear_cache(
        [
            page.full_url, # page
            page.get_parent().full_url, # category page
            page.get_url_parts()[1], # root page
        ]
    )
