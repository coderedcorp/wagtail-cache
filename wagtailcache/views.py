"""
Views for the wagtail admin dashboard.
"""
from typing import Dict
from typing import List

from django.core.cache import caches
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from wagtailcache.cache import clear_cache
from wagtailcache.settings import wagtailcache_settings


def index(request):
    """
    The wagtail-cache admin panel.
    """
    # Get the keyring to show cache contents.
    _wagcache = caches[wagtailcache_settings.WAGTAIL_CACHE_BACKEND]
    keyring: Dict[str, List[str]] = _wagcache.get("keyring", {})
    return render(
        request,
        "wagtailcache/index.html",
        {
            "keyring": keyring,
        },
    )


def clear(request):
    """
    Clear the cache and redirect back to the admin settings page.
    """
    clear_cache()
    return HttpResponseRedirect(reverse("wagtailcache_admin:index"))
