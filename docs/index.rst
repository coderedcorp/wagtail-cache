Wagtail Cache Documentation
===========================

Wagtail Cache is a simple page cache for Wagtail inspired by the Django cache middleware.
It provides an extremely fast way of serving pages with no database hits whatsoever.
It is customizable enough that the developer can determine whether or not to cache
on each individual request/response, or even on the Wagtail page models directly!

Wagtail Cache also provides a panel to show cache stats and clear the cache
from the wagtail admin under Settings > Cache.


Notes
-----

This cache feature was originally part of `coderedcms <https://github.com/coderedcorp/coderedcms>`_
and is in use successfully on live production sites.

Requires Wagtail >= 2.0


Contents
--------

.. toctree::
   :maxdepth: 2
   :titlesonly:

   getting_started/index
   releases/index
