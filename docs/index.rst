Wagtail Cache Documentation
===========================

Wagtail Cache is a simple page cache for Wagtail inspired by the Django cache
middleware. It provides an extremely fast way of serving pages with no database
hits whatsoever, and does not require any additional infrastructure (such as
Redis, Memcached, etc.)! However it is still customizable enough that the
developer can determine whether or not to cache on each individual
request/response, views, or Wagtail page models directly.

Wagtail Cache also provides a panel to show cache stats and clear the cache from
the wagtail admin under **Settings > Cache**.

`GitHub <https://github.com/coderedcorp/wagtail-cache>`_ |
`Documentation <https://docs.coderedcorp.com/wagtail-cache/>`_ |
`PyPI <https://pypi.org/project/wagtail-cache/>`_


Notes
-----

This cache feature was originally part of `coderedcms
<https://github.com/coderedcorp/coderedcms>`_ and is in use successfully on live
production sites.

Version 1.x supports Wagtail 2.

Version 2.x supports Wagtail 3.


Contents
--------

.. toctree::
   :maxdepth: 2
   :titlesonly:

   getting_started/index
   contributing
   releases
