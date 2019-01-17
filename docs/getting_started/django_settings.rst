Django Settings
===============

WAGTAIL_CACHE
-------------
Boolean toggling whether or not to load the page caching machinery and enable cache settings in
the wagtail admin. Defaults to ``True`` which is on. Most developers will want to set this to
``False`` in the development environment.

WAGTAIL_CACHE_BACKEND
---------------------
The name of the Django cache alias/backend to use for the page cache. Defaults to ``'default'``
which is required by Django when using the cache. Complex projects would likely want to use a
separate cache for the page cache to easily purge as needed without affecting other caches.
Clearing the cache through the wagtail admin will purge this entire cache.

WAGTAIL_CACHE_HEADER
--------------------
By default, an HTTP header named ``X-Wagtail-Cache`` is added to the response to indicate
a cache hit or miss. To turn off this header, set ``WAGTAIL_CACHE_HEADER = False``,
or to customize the header set to a string. Note that other HTTP headers may also added by
the Django cache middleware.
