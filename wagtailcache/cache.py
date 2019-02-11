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
                result = fn(request, is_cacheable)
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

                # check if the response is cacheable
                if response.has_header('Cache-Control'):
                    is_cacheable = 'no-cache' not in response['Cache-Control'] and \
                        'private' not in response['Cache-Control']
                for fn in hooks.get_hooks('is_response_cacheable'):
                    result = fn(response, is_cacheable)
                    if isinstance(result, bool):
                        is_cacheable = result

                if is_cacheable:
                    # cache the response
                    djcache.process_response(request, response)
                    # add a response header to indicate this was a cache miss
                    if wagtailcache_settings['WAGTAIL_CACHE_HEADER']:
                        response[wagtailcache_settings['WAGTAIL_CACHE_HEADER']] = 'miss'
                else:
                    # add a response header to indicate this was intentionally not cached
                    if wagtailcache_settings['WAGTAIL_CACHE_HEADER']:
                        response[wagtailcache_settings['WAGTAIL_CACHE_HEADER']] = 'skip'

                return response

        # as a fall-back, just run the view function.
        return view_func(request, *args, **kwargs)

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
        response['Cache-Control'] = 'private'
        return response

    def serve(self, request, *args, **kwargs):
        """
        Add a custom cache-control header, or set to private if the page is being served
        behind a view restriction.
        """
        response = super().serve(request, *args, **kwargs)
        if self.get_view_restrictions():
            response['Cache-Control'] = 'private'
        elif hasattr(self, 'cache_control'):
            if callable(self.cache_control):
                response['Cache-Control'] = self.cache_control()
            else:
                response['Cache-Control'] = self.cache_control
        return response
