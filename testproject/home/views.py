from django.http import HttpResponse
from wagtailcache.cache import cache_page, nocache_page


@cache_page
def cached_view(request):
    return HttpResponse("Hello, World!")


@nocache_page
def nocached_view(request):
    return HttpResponse("Hello, World!")
