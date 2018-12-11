Wagtail Hooks
=============

is_request_cacheable
--------------------
The callable passed into this hook should take a ``request`` argument, and return a
``bool`` indicating whether or not the response to this request should be cached
(served from the cache if it is already cached, or added to the cache if it is not already
cached). Not returning, or returning anything other than a bool will not affect the caching
decision. For example::

    from wagtail.core import hooks

    @hooks.register('is_request_cacheable')
    def nocache_in_query(request):
        # if the querystring contains a "nocache" key, return False to forcibly not cache.
        # otherwise, do not return to let wagtail-cache decide how to cache.
        if 'nocache' in request.GET:
            return False
