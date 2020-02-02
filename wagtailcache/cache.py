"""
Functionality to set, serve from, and clear the cache.
"""

from enum import Enum
from functools import wraps
from typing import Callable, Optional

from django.core.cache import caches
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse
from django.template.response import SimpleTemplateResponse
from django.utils.cache import (
    get_cache_key, get_max_age, has_vary_header, learn_cache_key,
    patch_response_headers,
)
from django.utils.deprecation import MiddlewareMixin
from wagtail.core import hooks

from wagtailcache.settings import wagtailcache_settings


class CacheControl(Enum):
    """
    "Cache-Control" header values.
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
    # Patch cache-control with no-cache if it is not already set.
    if status == Status.SKIP and not response.get("Cache-Control", None):
        response["Cache-Control"] = CacheControl.NOCACHE.value
    # Add our custom header.
    if wagtailcache_settings.WAGTAIL_CACHE_HEADER:
        response[wagtailcache_settings.WAGTAIL_CACHE_HEADER] = status.value


class FetchFromCacheMiddleware(MiddlewareMixin):
    """
    Loads a request from the cache if it exists.
    Mostly stolen from `django.middleware.cache.FetchFromCacheMiddleware`.
    """

    def __init__(self, get_response=None):
        self._wagcache = caches[wagtailcache_settings.WAGTAIL_CACHE_BACKEND]
        self.get_response = get_response

    def process_request(self, request: WSGIRequest) -> Optional[HttpResponse]:
        if not wagtailcache_settings.WAGTAIL_CACHE:
            return None

        # Check if request is cacheable
        # Only cache GET and HEAD requests.
        # Don't cache requests that are previews.
        # Don't cache reqeusts that have a logged in user.
        # NOTE: Wagtail manually adds `is_preview` to the request object. This
        #       not normally part of a request object.
        is_cacheable = \
            request.method in ('GET', 'HEAD') and \
            not getattr(request, 'is_preview', False) and \
            not request.user.is_authenticated

        # Allow the user to override our caching decision.
        for fn in hooks.get_hooks('is_request_cacheable'):
            result = fn(request, is_cacheable)
            if isinstance(result, bool):
                is_cacheable = result

        if not is_cacheable:
            setattr(request, "_wagtailcache_update", False)
            setattr(request, "_wagtailcache_skip", True)
            return None  # Don't bother checking the cache.

        # try and get the cached GET response
        cache_key = get_cache_key(request, None, 'GET', cache=self._wagcache)
        if cache_key is None:
            setattr(request, "_wagtailcache_update", True)
            return None  # No cache information available, need to rebuild.
        response = self._wagcache.get(cache_key)
        # if it wasn't found and we are looking for a HEAD, try looking just for that
        if response is None and request.method == 'HEAD':
            cache_key = get_cache_key(request, None, 'HEAD', cache=self._wagcache)
            response = self._wagcache.get(cache_key)

        if response is None:
            setattr(request, "_wagtailcache_update", True)
            return None  # No cache information available, need to rebuild.

        # hit, return cached response
        setattr(request, "_wagtailcache_update", False)
        # Add a response header to indicate this was a cache hit
        _patch_header(response, Status.HIT)
        return response


class UpdateCacheMiddleware(MiddlewareMixin):
    """
    Saves a response to the cache.
    Mostly stolen from `django.middleware.cache.UpdateCacheMiddleware`.
    """

    def __init__(self, get_response=None):
        self._wagcache = caches[wagtailcache_settings.WAGTAIL_CACHE_BACKEND]
        self.get_response = get_response

    def process_response(self, request: WSGIRequest, response: HttpResponse) -> HttpResponse:
        if not wagtailcache_settings.WAGTAIL_CACHE:
            return response

        if getattr(request, "_wagtailcache_skip", False):
            # If we should skip this response, add header and return.
            _patch_header(response, Status.SKIP)
            return response

        if not getattr(request, "_wagtailcache_update", False):
            # We don't need to update the cache, just return.
            return response

        # Check if the response is cacheable
        # Don't cache private or no-cache responses.
        # Do cache 200, 301, 302, 304, and 404 codes so that wagtail doesn't
        #   have to repeatedly look up these URLs in the database.
        # Don't cache streaming responses.
        is_cacheable = \
            CacheControl.NOCACHE.value not in response.get("Cache-Control", "") and \
            CacheControl.PRIVATE.value not in response.get("Cache-Control", "") and \
            response.status_code in (200, 301, 302, 304, 404) and \
            not response.streaming
        # Don't cache 200 responses that set a user-specific cookie in response to
        # a cookie-less request (e.g. CSRF tokens).
        if is_cacheable and response.status_code == 200:
            is_cacheable = not (
                not request.COOKIES and response.cookies and has_vary_header(response, 'Cookie')
            )

        # Allow the user to override our caching decision.
        for fn in hooks.get_hooks('is_response_cacheable'):
            result = fn(response, is_cacheable)
            if isinstance(result, bool):
                is_cacheable = result

        # If we are not allowed to cache the response, just return.
        if not is_cacheable:
            # Add a response header to indicate this was intentionally not cached.
            _patch_header(response, Status.SKIP)
            return response

        # Try to get the timeout from the "max-age" section of the "Cache-
        # Control" header before reverting to using the cache's default.
        timeout = get_max_age(response)
        if timeout is None:
            timeout = self._wagcache.default_timeout
        patch_response_headers(response, timeout)
        if timeout:
            cache_key = learn_cache_key(request, response, timeout, None, cache=self._wagcache)
            if isinstance(response, SimpleTemplateResponse):
                response.add_post_render_callback(
                    lambda r: self._wagcache.set(cache_key, r, timeout)
                )
            else:
                self._wagcache.set(cache_key, response, timeout)

            # Add a response header to indicate this was a cache miss.
            _patch_header(response, Status.MISS)

        return response


def clear_cache() -> None:
    """
    Clears the entire cache backend used by wagtail-cache.
    """
    if wagtailcache_settings.WAGTAIL_CACHE:
        caches[wagtailcache_settings.WAGTAIL_CACHE_BACKEND].clear()


def cache_page(view_func: Callable[..., HttpResponse]):
    """
    Decorator that determines whether or not to cache a page or serve a cached page.
    """
    @wraps(view_func)
    def _wrapped_view_func(request: WSGIRequest, *args, **kwargs) -> HttpResponse:
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
    def _wrapped_view_func(request: WSGIRequest, *args, **kwargs) -> HttpResponse:
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
        response = super().serve_password_required_response(request, form, action_url)
        response["Cache-Control"] = CacheControl.PRIVATE.value
        return response

    def serve(self, request, *args, **kwargs):
        """
        Add a custom cache-control header, or set to private if the page is being served
        behind a view restriction.
        """
        response = super().serve(request, *args, **kwargs)
        if self.get_view_restrictions():
            response["Cache-Control"] = CacheControl.PRIVATE.value
        elif hasattr(self, "cache_control"):
            if callable(self.cache_control):
                response["Cache-Control"] = self.cache_control()
            else:
                response["Cache-Control"] = self.cache_control
        return response
