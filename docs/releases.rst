=============
Release Notes
=============

2.4.0
=====

* Support Wagtail 6 and Django 5.1

2.3.0
=====

* Support Wagtail 5 and Django 4.2.

* Remove ``django-redis`` compatibility backend. Django 4.0+ has a native redis backend.


2.2.0
=====

* Support Wagtail 4 and Django 4.1.


2.1.1
=====

* Fix Django deprecation warnings.

* Previously, the feature to strip cookies was not triggered if the Vary header
  contained something other than "Cookie", e.g. ``Vary: Language, Cookie``. This
  change properly inspects and rebuilds the Vary header in such cases.


2.1.0
=====

This release massively improves caching for sites which employ trackers such as
Google Analytics, Facebook Pixel, HubSpot, etc.

* Add setting to strip cookies from requests and remove ``Vary: Cookie`` headers
  (except for Django session and CSRF token) to maximize caching opportunities.
  This is ON by default! See :ref:`WAGTAIL_CACHE_IGNORE_COOKIES`.

2.0.0
=====

* Includes everything from 1.1.0 released in tandem.

* Includes new SVG icon in settings panel. Previously this icon was either the
  cog, or the lighthing bolt if ``wagtailfontawesome`` was installed.

* Supports Wagtail 3 and only Wagtail 3. Wagtail 2 support will be maintained in
  the 1.x series as needed.


1.2.1
=====

* Previously, the feature to strip cookies was not triggered if the Vary header
  contained something other than "Cookie", e.g. ``Vary: Language, Cookie``. This
  change properly inspects and rebuilds the Vary header in such cases.


1.2.0
=====

This release massively improves caching for sites which employ trackers such as
Google Analytics, Facebook Pixel, HubSpot, etc.

* Add setting to strip cookies from requests and remove ``Vary: Cookie`` headers
  (except for Django session and CSRF token) to maximize caching opportunities.
  This is ON by default! See :ref:`WAGTAIL_CACHE_IGNORE_COOKIES`.


1.1.0
=====

New features

* Show list of all URLs cached in the Wagtail Admin.

* Support purging individual URLs (via regular expressions) from the cache. See
  :ref:`purge_specific_urls`.

* Ignore tracking querystring parameters by default. This means that pages with
  unique tracking parameters will still be cached and/or served from the cache
  regardless of those parameters. This should massively improve performance on
  sites with heavy marketing activity, but can potentially introduce breakage if
  you have server-side logic that uses tracking codes via the querystring.

  The list of querystrings to ignore can be customized, or the feature can be
  completely disabled. See Django setting :ref:`WAGTAIL_CACHE_IGNORE_QS`.

Bug fixes

* Previously, request with methods except GET and HEAD were never cached, even
  if you override the caching decision with ``is_request_cacheable`` hooks.
  These requests are still not cached by default, but *can be cached* if you
  override the caching decision. Please use caution when overriding caching
  decisions using :doc:`these hooks </getting_started/hooks>`.

Maintenance


* Add support for Django 4.

* Supports Wagtail 2 only.

* New shiny documentation based on the Wagtail Sphinx theme.


1.0.2
=====

* Fix typo in Wagtail Cache settings page.

* Updated unit tests for Wagtail 2.12.

* Apply ``black`` formatting to codebase.

.. note::

    Wagtail Cache may not work correctly with
    ``wagtail.core.middleware.SiteMiddleware`` or
    ``wagtail.contrib.legacy.sitemiddleware.SiteMiddleware`` on Wagtail 2.9 and
    newer. `Follow these instructions to replace SiteMiddleware
    <https://docs.wagtail.io/en/stable/releases/2.9.html#sitemiddleware-and-request-site-deprecated>`_.


1.0.1
=====

* Support Django installations where ``AuthenticationMiddleware`` is not enabled.
  In this situation, it will behave the same as if no user is logged in.
* Packaging and documentation cleanup.


1.0.0
=====

There are no functionality changes for this release. However at this point
the package is mature and well tested enough to designate a 1.0 version.

* Support Django 3.0.
* Add unit tests, type hints, and continuous integration.

As a result of the unit tests, a few minor changes have been implemented under
the hood:

* Refactored ``wagtailcache.settings.wagtailcache_settings`` to be an object,
  similar to Django ``settings``, rather than a dictionary.
* Add ``wagtailcache.cache.Status`` and ``wagtailcache.cache.CacheControl``
  enums to replace hard-coded string values.
* Always set a "Cache-Control" header when skipping the cache to signal the
  caching decision to upstream caches.


0.5.2
=====

* Add new management command `clear_wagtail_cache` to clear cache.
* Minor code cleanup.


0.5.1
=====

* Ignore ``Vary: Cookie`` header when caching 301, 302, 304, and 404 response codes. Always served cached responses regardless of cookies.


0.5.0
=====

* Added new middleware. This is now the recommended way of using Wagtail Cache. See :doc:`/getting_started/install`.
* The middleware will additionally cache 404 and 301/302 responses, to lighten the load on your database.
* The middleware will intelligently handle CSRF tokens and only cache those responses based on the cookie.
  So the new middleware should completely eliminate any CSRF token issues while also being able to cache those pages.
* The middleware now processes all cacheable requests/responses, not just wagtail pages. To revert to previous
  behavior, continue using the decorator.


0.4.0
=====

* Added new ``is_response_cacheable`` hook. See :doc:`/getting_started/hooks`.
* Never cache responses with a ``Cache-Control`` header containing ``no-cache`` or ``private``.
* New ``WagtailCacheMixin`` to support Page models with privacy or view restrictions. See :doc:`/getting_started/install`.
* Documentation updates and clarification.


0.3.0
=====

* Add support for ``django-redis`` cache backend. See :doc:`/getting_started/supported_backends`.
* Add __init__.py in ``templatetags`` directory.
* ``is_request_cacheable`` hook now passes the previous caching decision in as an argument. See :doc:`/getting_started/hooks`.
* Documentation updates.


0.2.1
=====

* Fixed packaging issue that resulted in HTML templates missing from 0.2.0 pip package.


0.2.0
=====

* Moved ``cache_page()`` and ``clear_cache()`` from ``wagtailcache`` to ``wagtailcache.cache``.
* New documentation! https://docs.coderedcorp.com/wagtail-cache/


0.1.0
=====

* Initial release
