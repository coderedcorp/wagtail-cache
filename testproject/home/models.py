from wagtail.models import Page
from wagtailcache.cache import WagtailCacheMixin


class WagtailPage(Page):
    """
    Normal page that does not include the mixin. This page should still be
    cached due to the middleware, but will not have the ability to provide
    custom cache instructions or "smart" caching features.
    """

    template = "home/page.html"


class CachedPage(WagtailCacheMixin, Page):
    """
    Represents a normal use-case.
    """

    template = "home/page.html"


class CacheControlPage(WagtailCacheMixin, Page):
    """
    Page that should never cache and should generate a custom
    cache-control header.
    """

    template = "home/page.html"
    cache_control = "no-cache"


class CallableCacheControlPage(WagtailCacheMixin, Page):
    """
    Page that should never cache and should generate a custom
    cache-control header via a function call.
    """

    template = "home/page.html"

    def cache_control(self):
        return "private"


class CookiePage(WagtailCacheMixin, Page):
    """
    Page that sets a random cookie, hence should not be served from cached
    when a cookie-less request is given (unless WAGTAIL_CACHE_IGNORE_COOKIES is
    set)
    """

    template = "home/page.html"

    def serve(self, request):
        response = super().serve(request)
        response.set_cookie("c_is_for", "cookie")
        return response


class CsrfPage(WagtailCacheMixin, Page):
    """
    Page that sets a CSRF token (cookie), hence should never be served from
    the cache when a cookie-less request is given.
    """

    template = "home/csrf_page.html"
