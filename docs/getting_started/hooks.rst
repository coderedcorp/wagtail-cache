Wagtail Hooks
=============

is_request_cacheable
--------------------
The callable passed into this hook should take an ``HttpRequest`` and a ``bool`` argument, and returns a
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
        # if the querystring contains a "nocache" key, return False to
        # forcibly not cache. Otherwise, do not return to let wagtail-cache
        # decide how to cache.
        if 'nocache' in request.GET:
            return False


is_response_cacheable
---------------------
The callable passed into this hook should take an ``HttpResponse`` and a ``bool`` argument, and returns a
``bool`` indicating whether or not this response should be cached (added to the cache if it is not already
cached). Not returning, or returning anything other than a bool will not affect the caching
decision. The ``bool`` passed in represents the current caching decision. So if there were multiple
``is_response_cacheable`` hooks called, each one would receive the result of the previous. Use this
variable as you see fit to help with your own logic.

For example::

    from wagtail.core import hooks

    @hooks.register('is_response_cacheable')
    def nocache_secrets(request, curr_cache_decision):
        # if the response contains a custom header, return False to
        # forcibly not cache. Otherwise, do not return to let wagtail-cache
        # decide how to cache.
        if response.has_header('X-My-Header'):
            if response['X-My-Header'] == 'secret':
                return False


Notes about the request/response cycle
--------------------------------------

During a request/response cycle, wagtail-cache makes its caching decision as so:

#. If the request is not a preview, does not have a logged in user, and is GET or HEAD, then try to cache.
#. Run ``is_request_cacheable`` hooks.
#. If the result of the hooks is ``True``, then check to see if this request is already in the cache.
#. If the request is already in the cache, serve directly from the cache.
#. If the request is not in the cache, then run the view.
#. Check if the view's response contains a ``Cache-Control`` header containing ``private`` or ``no-cache``.
#. Run ``is_response_cacheable`` hooks.
#. If the result of the hooks is ``True``, then save the response into the cache for next time.
#. Finally, return the response.
