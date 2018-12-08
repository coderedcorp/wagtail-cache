from django.urls import include, path, reverse
from django.utils.translation import ugettext_lazy as _
from wagtail.admin.menu import MenuItem
from wagtail.core import hooks

from wagtailcache import cache_icon, urls


class CacheMenuItem(MenuItem):
    def is_shown(self, request):
        return request.user.is_superuser


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        path('cache/', include((urls, 'wagtailcache'), namespace='wagtailcache_admin')),
    ]


@hooks.register('register_settings_menu_item')
def register_cache_menu():
    return CacheMenuItem(_('Cache'), reverse('wagtailcache_admin:index'), classnames='icon icon-' + cache_icon)
