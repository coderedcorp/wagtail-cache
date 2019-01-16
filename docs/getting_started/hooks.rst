Wagtail Hooks
=============

is_request_cacheable
--------------------
The callable passed into this hook should take a ``request`` and a ``bool`` argument, and returns a
``bool`` indicating whether or not the response to this request should be cached
(served from the cache if it is already cached, or added to the cache if it is not already
cached). Not returning, or returning anything other than a bool will not affect the caching
decision. The ``bool`` passed in represents the current caching decision. So if there were multiple
``is_request_cacheable`` hooks called, each one would receive the result of the previous. Use this
variable as you see fit to help with your own logic.

For example::

    from wagtail.core import hooks

    @hooks.register('is_request_cacheable')
    def nocache_in_query(request, curr_cache_decision):
        # if the querystring contains a "nocache" key, return False to forcibly not cache.
        # otherwise, do not return to let wagtail-cache decide how to cache.
        if 'nocache' in request.GET:
            return False
