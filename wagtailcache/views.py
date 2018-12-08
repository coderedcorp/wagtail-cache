from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from wagtailcache import cache_icon, clear_cache


def index(request):
    return render(request, 'wagtailcache/index.html', {'cache_icon': cache_icon})

def clear(request):
    clear_cache()
    return HttpResponse("Cache has been cleared.")
