"""
Views for the wagtail admin dashboard.
"""

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from wagtailcache.cache import clear_cache
from wagtailcache.models import KeyringItem


def index(request):
    """
    The wagtail-cache admin panel.
    """
    # Get the keyring to show cache contents.
    keyring = KeyringItem.objects.active()
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
