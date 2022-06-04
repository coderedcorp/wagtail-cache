Django Settings
===============

WAGTAIL_CACHE
-------------

Boolean toggling whether or not to load the page caching machinery and enable
cache settings in the wagtail admin. Defaults to ``True`` which is on. Most
developers will want to set this to ``False`` in the development environment.

WAGTAIL_CACHE_BACKEND
---------------------

The name of the Django cache alias/backend to use for the page cache; one of the
keys in the ``CACHES`` Django setting. Defaults to ``'default'`` which is
required by Django when using the cache. Complex projects would likely want to
use a separate cache for the page cache to easily purge as needed without
affecting other caches. Clearing the cache through the wagtail admin will purge
this entire cache.

WAGTAIL_CACHE_HEADER
--------------------

By default, an HTTP header named ``X-Wagtail-Cache`` is added to the response to
indicate a cache hit or miss. To turn off this header, set
``WAGTAIL_CACHE_HEADER = False``, or to customize the header set to a string.
Note that other HTTP headers may also be added by the Django cache middleware.

WAGTAIL_CACHE_IGNORE_QS
-----------------------

.. versionadded:: 2.0

   This setting will ignore tracking/advertising URL paramters, and is ON by
   default. To restore the old behavior, set to ``None``.

A list of strings (regular expressions) to ignore from the URL querystring when
determining the caching decision. Any querystrings in this list **MUST NOT**
have any effect on how your pages/views are served.

By default this is set to a list of well-known tracking and advertising tags
such used by Google Analytics, Facebook, HubSpot, etc. These tracking codes are
a sysadmin's worst nightmare as they effectively bust any semblance of a cache
and senselessly spike server load. `The defaults are defined here
<https://github.com/coderedcorp/wagtail-cache/blob/main/wagtailcache/settings.py>`_.

If you use these querystring paramters for server-side logic, or if you find
that Wagtail Cache is serving incorrect page contents, you may need to customize
or disable this setting.

To restore the old behavior, and treat each combination of querystrings as its
own unique page in the cache, set this value to ``None`` or ``[]``.

If you feel as though the spammers have won, and want the nuclear option, you
can set this to ``[r".*"]`` which will ignore all querystrings. This is surely
a terrible idea, but it can be done.
