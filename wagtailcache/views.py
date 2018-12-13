"""
Views for the wagtail admin dashbaord.
"""

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from wagtailcache.cache import clear_cache
from wagtailcache.icon import CACHE_ICON


def index(request):
    """
    The wagtail-cache admin panel.
    """
    return render(request, 'wagtailcache/index.html', {'cache_icon': CACHE_ICON})

def clear(request):
    """
    AJAX call to clear the cache.
    """
    clear_cache()
    return HttpResponse(_("Cache has been cleared."))
