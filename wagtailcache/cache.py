"""
Functionality to set, serve from, and clear the cache.
"""

from functools import wraps
from django.core.cache import caches
from django.middleware.cache import CacheMiddleware
from wagtail.core import hooks

from wagtailcache.settings import wagtailcache_settings


def clear_cache():
    """
    Clears the entire cache backend used by wagtail-cache.
    """
    if wagtailcache_settings['WAGTAIL_CACHE']:
        cache = caches[wagtailcache_settings['WAGTAIL_CACHE_BACKEND']]
        cache.clear()


def cache_page(view_func):
    """
    Decorator that determines whether or not to cache a page or serve a cached page.
    """
    @wraps(view_func)
    def _wrapped_view_func(request, *args, **kwargs):
        if wagtailcache_settings['WAGTAIL_CACHE']:

            # check if request is cacheable
            request.is_preview = getattr(request, 'is_preview', False)
            is_cacheable = request.method in ('GET', 'HEAD') and \
                not request.is_preview and \
                not request.user.is_authenticated
            for fn in hooks.get_hooks('is_request_cacheable'):
                result = fn(request)
                if isinstance(result, bool):
                    is_cacheable = result

            if is_cacheable:
                cache = caches[wagtailcache_settings['WAGTAIL_CACHE_BACKEND']]
                # Create a CacheMiddleware using our specified values
                djcache = CacheMiddleware(
                    cache_alias=wagtailcache_settings['WAGTAIL_CACHE_BACKEND'],
                    cache_timeout=cache.default_timeout,
                    key_prefix=None
                )
                response = djcache.process_request(request)
                if response:
                    # add a response header to indicate this was a cache hit
                    if wagtailcache_settings['WAGTAIL_CACHE_HEADER']:
                        response[wagtailcache_settings['WAGTAIL_CACHE_HEADER']] = 'hit'
                    return response

                # since we don't have a response at this point, run the view.
                response = view_func(request, *args, **kwargs)
                # add a response header to indicate this was a cache miss
                if wagtailcache_settings['WAGTAIL_CACHE_HEADER']:
                    response[wagtailcache_settings['WAGTAIL_CACHE_HEADER']] = 'miss'
                djcache.process_response(request, response)

                return response

        # as a fall-back, just run the view function.
        return view_func(request, *args, **kwargs)

    return _wrapped_view_func
