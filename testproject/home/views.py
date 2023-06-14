from django.http import HttpResponse
from django.template.response import TemplateResponse

from wagtailcache.cache import cache_page
from wagtailcache.cache import nocache_page


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


@cache_page
def template_response_view(request):
    response = TemplateResponse(request, "home/page.html", {})
    return response
