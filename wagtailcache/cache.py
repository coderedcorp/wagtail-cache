"""
Functionality to set, serve from, and clear the cache.
"""
import re
from enum import Enum
from functools import wraps
from typing import Callable
from typing import List
from typing import Optional
from urllib.parse import unquote

from django.conf import settings
from django.core.cache import caches
from django.core.cache.backends.base import BaseCache
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse
from django.template.response import SimpleTemplateResponse
from django.utils.cache import cc_delim_re
from django.utils.cache import get_cache_key
from django.utils.cache import get_max_age
from django.utils.cache import has_vary_header
from django.utils.cache import learn_cache_key
from django.utils.cache import patch_response_headers
from django.utils.deprecation import MiddlewareMixin
from wagtail import hooks

from wagtailcache.settings import wagtailcache_settings


class CacheControl(Enum):
    """
    ``Cache-Control`` header values.
    """

    NOCACHE = "no-cache"
    PRIVATE = "private"


class Status(Enum):
    """
    WAGTAIL_CACHE_HEADER header values.
    """

    HIT = "hit"
    MISS = "miss"
    SKIP = "skip"


def _patch_header(response: HttpResponse, status: Status) -> None:
    """
    Adds our Cache Control status to the response headers.
    """
    # Patch cache-control with no-cache if it is not already set.
    if status == Status.SKIP and not response.get("Cache-Control", None):
        response["Cache-Control"] = CacheControl.NOCACHE.value
    # Add our custom header.
    if wagtailcache_settings.WAGTAIL_CACHE_HEADER:
        response[wagtailcache_settings.WAGTAIL_CACHE_HEADER] = status.value


def _delete_vary_cookie(response: HttpResponse) -> None:
    """
    Deletes the ``Vary: Cookie`` header while keeping other items of the
    Vary header in tact. Inspired by ``django.utils.cache.patch_vary_headers``.
    """
    if not response.has_header("Vary"):
        return
    # Parse the value of Vary header.
    vary_headers = cc_delim_re.split(response["Vary"])
    # Build a lowercase-keyed dict to preserve the original case.
    vhdict = {}
    for item in vary_headers:
        vhdict.update({item.lower(): item})
    # Delete "Cookie".
    if "cookie" in vhdict:
        del vhdict["cookie"]
        # Delete the header if it's now empty.
        if not vhdict:
            del response["Vary"]
            return
        # Else patch the header.
        vary_headers = [vhdict[k] for k in vhdict]
        response["Vary"] = ", ".join(vary_headers)


def _chop_querystring(r: WSGIRequest) -> WSGIRequest:
    """
    Given a request object, remove any of our ignored querystrings from it.
    """
    if len(r.GET) and wagtailcache_settings.WAGTAIL_CACHE_IGNORE_QS:
        # Make a copy of querystrings, and delete any that should be ignored.
        qs = r.GET.copy()
        for q in r.GET:
            for regex in wagtailcache_settings.WAGTAIL_CACHE_IGNORE_QS:
                if re.match(regex, q):
                    del qs[q]
        # Mutate the request to include our chopped up querystrings. We must
        # also mutate the raw QUERY_STRING as that is used within
        # ``request.build_absolute_uri()`` which is used in Django cache
        # middleware internals.
        r.GET = qs
        r.META["QUERY_STRING"] = qs.urlencode()
    return r


def _chop_cookies(r: WSGIRequest) -> WSGIRequest:
    """
    If the request contains cookies which are not native to Django, remove them.
    """
    if not wagtailcache_settings.WAGTAIL_CACHE_IGNORE_COOKIES:
        return r

    if r.COOKIES and not (
        settings.CSRF_COOKIE_NAME in r.COOKIES
        or settings.SESSION_COOKIE_NAME in r.COOKIES
    ):
        r.COOKIES = {}
    return r


def _chop_response_vary(r: WSGIRequest, s: HttpResponse) -> HttpResponse:
    """
    In many situations Django adds ``Vary: Cookie``, however, nearly all
    tracking software (Google, HubSpot, etc.) litters worthless crap into the
    cookies which ends up busting our cache, making it effectively impossible to
    cache anything. With this special setting, we are going to forcibly remove
    the ``Vary: Cookie`` header unless the cookie contains a recognizable Django
    session or CSRF token.
    """
    if not wagtailcache_settings.WAGTAIL_CACHE_IGNORE_COOKIES:
        return s

    if (
        not s.has_header("Set-Cookie")
        and s.has_header("Vary")
        and has_vary_header(s, "Cookie")
        and not (
            settings.CSRF_COOKIE_NAME in s.cookies
            or settings.CSRF_COOKIE_NAME in r.COOKIES
            or settings.SESSION_COOKIE_NAME in s.cookies
            or settings.SESSION_COOKIE_NAME in r.COOKIES
        )
    ):
        _delete_vary_cookie(s)
    return s


def _get_cache_key(r: WSGIRequest, c: BaseCache) -> str:
    """
    Wrapper for Django's get_cache_key which first strips specific
    querystrings. Since the Django cache middleware is somewhat complicated and
    RFC compliant, we are best off to chop and pass it along rather than
    re-inventing the cache keying logic.
    """
    r = _chop_querystring(r)
    r = _chop_cookies(r)
    return get_cache_key(r, None, r.method, c)


def _learn_cache_key(
    r: WSGIRequest, s: HttpResponse, t: int, c: BaseCache
) -> str:
    """
    Wrapper for Django's learn_cache_key which first strips specific
    querystrings. Since the Django cache middleware is somewhat complicated and
    RFC compliant, we are best off to chop and pass it along rather than
    re-inventing the cache keying logic.
    """
    r = _chop_querystring(r)
    r = _chop_cookies(r)
    return learn_cache_key(r, s, t, None, c)


class FetchFromCacheMiddleware(MiddlewareMixin):
    """
    Loads a request from the cache if it exists.
    Mostly stolen from ``django.middleware.cache.FetchFromCacheMiddleware``.
    """

    def __init__(self, get_response=None):
        self._wagcache = caches[wagtailcache_settings.WAGTAIL_CACHE_BACKEND]
        self.get_response = get_response
        self._async_check()

    def process_request(self, request: WSGIRequest) -> Optional[HttpResponse]:
        if not wagtailcache_settings.WAGTAIL_CACHE:
            return None
        # Check if request is cacheable
        # Only cache GET and HEAD requests.
        # Don't cache requests that are previews.
        # Don't cache requests that have a logged in user.
        # NOTE: Wagtail manually adds `is_preview` to the request object.
        #       This is not normally part of a request object.
        is_cacheable = (
            request.method in ("GET", "HEAD")
            and not getattr(request, "is_preview", False)
            and not (hasattr(request, "user") and request.user.is_authenticated)
        )
        # Allow the user to override our caching decision.
        for fn in hooks.get_hooks("is_request_cacheable"):
            result = fn(request, is_cacheable)
            if isinstance(result, bool):
                is_cacheable = result

        if not is_cacheable:
            setattr(request, "_wagtailcache_update", False)
            setattr(request, "_wagtailcache_skip", True)
            return None  # Don't bother checking the cache.
        # Try and get the cached response.
        cache_key = _get_cache_key(request, self._wagcache)
        if cache_key is None:
            setattr(request, "_wagtailcache_update", True)
            return None  # No cache information available, need to rebuild.

        response = self._wagcache.get(cache_key)

        if response is None:
            setattr(request, "_wagtailcache_update", True)
            return None  # No cache information available, need to rebuild.
        # Hit. Return cached response.
        setattr(request, "_wagtailcache_update", False)
        return response


class UpdateCacheMiddleware(MiddlewareMixin):
    """
    Saves a response to the cache.
    Mostly stolen from ``django.middleware.cache.UpdateCacheMiddleware``.
    """

    def __init__(self, get_response=None):
        self._wagcache = caches[wagtailcache_settings.WAGTAIL_CACHE_BACKEND]
        self.get_response = get_response
        self._async_check()

    def process_response(
        self, request: WSGIRequest, response: HttpResponse
    ) -> HttpResponse:
        if not wagtailcache_settings.WAGTAIL_CACHE:
            return response

        if (
            hasattr(request, "_wagtailcache_skip")
            and request._wagtailcache_skip
        ):
            # If we should skip this response, add header and return.
            _patch_header(response, Status.SKIP)
            return response

        if (
            hasattr(request, "_wagtailcache_update")
            and not request._wagtailcache_update
        ):
            # Add a response header to indicate this was a cache hit.
            _patch_header(response, Status.HIT)
            # Potentially remove the ``Vary: Cookie`` header.
            _chop_response_vary(request, response)
            # We don't need to update the cache, just return.
            return response
        # Check if the response is cacheable
        # Don't cache private or no-cache responses.
        # Do cache 200, 301, 302, 304, and 404 codes so that wagtail doesn't
        #   have to repeatedly look up these URLs in the database.
        # Don't cache streaming responses.
        # Don't cache responses that set a user-specific cookie in response
        #   to a cookie-less request (e.g. CSRF tokens).
        is_cacheable = (
            CacheControl.NOCACHE.value not in response.get("Cache-Control", "")
            and CacheControl.PRIVATE.value
            not in response.get("Cache-Control", "")
            and response.status_code in (200, 301, 302, 304, 404)
            and not response.streaming
            and not (
                not request.COOKIES
                and response.cookies
                and has_vary_header(response, "Cookie")
            )
        )
        # Allow the user to override our caching decision.
        for fn in hooks.get_hooks("is_response_cacheable"):
            result = fn(response, is_cacheable)
            if isinstance(result, bool):
                is_cacheable = result
        # If we are not allowed to cache the response, just return.
        if not is_cacheable:
            # Add response header to indicate this was intentionally not cached.
            _patch_header(response, Status.SKIP)
            return response
        # Potentially remove the ``Vary: Cookie`` header.
        _chop_response_vary(request, response)
        # Try to get the timeout from the ``max-age`` section of the
        # ``Cache-Control`` header before reverting to using the cache's
        # default.
        timeout = get_max_age(response)
        if timeout is None:
            timeout = self._wagcache.default_timeout
        patch_response_headers(response, timeout)
        if timeout:
            cache_key = _learn_cache_key(
                request, response, timeout, self._wagcache
            )
            # Track cache keys based on URI.
            # (of the chopped request, not the real one).
            cr = _chop_querystring(request)
            uri = unquote(cr.build_absolute_uri())
            keyring = self._wagcache.get("keyring", {})
            # Get current cache keys belonging to this URI.
            # This should be a list of keys.
            uri_keys: List[str] = keyring.get(uri, [])
            # Append the key to this list and save.
            uri_keys.append(cache_key)
            keyring[uri] = uri_keys
            self._wagcache.set("keyring", keyring)

            if isinstance(response, SimpleTemplateResponse):

                def callback(r):
                    self._wagcache.set(cache_key, r, timeout)

                response.add_post_render_callback(callback)
            else:
                self._wagcache.set(cache_key, response, timeout)
            # Add a response header to indicate this was a cache miss.
            _patch_header(response, Status.MISS)

        return response


def clear_cache(urls: List[str] = []) -> None:
    """
    Clears the Wagtail cache backend.

    :param urls: An optional list of strings, representing regular expressions
    to match against the list of URLs in the cache. If a URL matches, it is
    deleted from the cache. If ``urls`` is ``None`` the entire cache is cleared.
    """

    if not wagtailcache_settings.WAGTAIL_CACHE:
        return

    _wagcache = caches[wagtailcache_settings.WAGTAIL_CACHE_BACKEND]
    if urls and "keyring" in _wagcache:
        keyring = _wagcache.get("keyring")
        # Check the provided URL matches a key in our keyring.
        matched_urls = []
        for regex in urls:
            for key in keyring:
                if re.match(regex, key):
                    matched_urls.append(key)
        # If it matches, delete each entry from the cache,
        # and delete the URL from the keyring.
        for url in matched_urls:
            entries = keyring.get(url, [])
            for cache_key in entries:
                _wagcache.delete(cache_key)
            del keyring[url]
        # Save the keyring.
        _wagcache.set("keyring", keyring)
    # Clears the entire cache backend used by wagtail-cache.
    else:
        _wagcache.clear()


def cache_page(view_func: Callable[..., HttpResponse]):
    """
    Decorator that determines whether or not to cache a page or serve a cached
    page.
    """

    @wraps(view_func)
    def _wrapped_view_func(
        request: WSGIRequest, *args, **kwargs
    ) -> HttpResponse:
        # Try to fetch an already cached page from wagtail-cache.
        response = FetchFromCacheMiddleware().process_request(request)
        if response:
            return response
        # Since we don't have a response at this point, process the request.
        response = view_func(request, *args, **kwargs)
        # Cache the response.
        response = UpdateCacheMiddleware().process_response(request, response)
        return response

    return _wrapped_view_func


def nocache_page(view_func: Callable[..., HttpResponse]):
    """
    Decorator that sets no-cache on all responses.
    """

    @wraps(view_func)
    def _wrapped_view_func(
        request: WSGIRequest, *args, **kwargs
    ) -> HttpResponse:
        # Run the view.
        response = view_func(request, *args, **kwargs)
        # Set cache-control if wagtail-cache is enabled.
        if wagtailcache_settings.WAGTAIL_CACHE:
            _patch_header(response, Status.SKIP)
        return response

    return _wrapped_view_func


class WagtailCacheMixin:
    """
    Add cache-control headers to various Page responses that could be returned.
    """

    def serve_password_required_response(self, request, form, action_url):
        """
        Add a cache-control header if the page requires a password.
        """
        response = super().serve_password_required_response(  # type: ignore
            request, form, action_url
        )
        response["Cache-Control"] = CacheControl.PRIVATE.value
        return response

    def serve(self, request, *args, **kwargs):
        """
        Add a custom cache-control header, or set to private if the page is
        being served behind a view restriction.
        """
        response = super().serve(request, *args, **kwargs)  # type: ignore
        if self.get_view_restrictions():  # type: ignore
            response["Cache-Control"] = CacheControl.PRIVATE.value
        elif hasattr(self, "cache_control"):
            if callable(self.cache_control):
                response["Cache-Control"] = self.cache_control()
            else:
                response["Cache-Control"] = self.cache_control
        return response
