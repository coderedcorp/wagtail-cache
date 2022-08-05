from django.http import HttpResponse
from wagtailcache.cache import cache_page, nocache_page


@cache_page
def cached_view(request):
    return HttpResponse("Hello, World!")


@nocache_page
def nocached_view(request):
    return HttpResponse("Hello, World!")


def vary_view(request):
    r = HttpResponse("Variety is the spice of life.")
    r.headers["Vary"] = "A, B, Cookie, C"
    return r
