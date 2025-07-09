Installation
============

1. Install
----------

.. code-block:: console

   $ pip install wagtail-cache

Add to installed apps in the project settings:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        'wagtailcache',
        ...
    ]

Enable the middleware. ``UpdateCacheMiddleware`` must come FIRST and
``FetchFromCacheMiddleware`` must come LAST in the list of middleware to
correctly cache everything:

.. code-block:: python

    MIDDLEWARE = [
        'wagtailcache.cache.UpdateCacheMiddleware',

        ...

        'wagtailcache.cache.FetchFromCacheMiddleware',
    ]

Do not use the Wagtail Cache middleware with the Django cache middleware. If you
are currently using the Django cache middleware, you should remove it before
adding the Wagtail Cache middleware. Note: Adding 'FetchFromCacheMiddleware' blocks 
django-browser-reload (if installed) from watching your project.


2. Define a cache
-----------------

Next a cache must be configured in the settings. Here is an example file cache,
which is suitable for use on any web server:

.. code-block:: python

    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
            "LOCATION": BASE_DIR / "cache",
            "KEY_PREFIX": "wagtailcache",
            "TIMEOUT": 4 * 60 * 60,  # 4 hours (in seconds)
        }
    }

.. note::

   ``TIMEOUT`` is used both for the timeout in the cache backend, and for the
   Cache-Control max-age sent to the browser. Therefore it must be a positive
   integer, and cannot be ``None``.


3. Instruct pages how to cache
------------------------------

There are many situations where a specific page should not be cached. For
example, a page with privacy or view restrictions (e.g. password, login
required), or possibly a form or other page with CSRF data.

For that reason, it is recommended to add the ``WagtailCacheMixin`` to your Page
models, which will handle all of these situations and provide additional control
over how and when pages cache.

Add the mixin **to the beginning** of the class inheritance:

.. code-block:: python

    from wagtailcache.cache import WagtailCacheMixin

    class MyPage(WagtailCacheMixin, Page):
        ...


Now ``MyPage`` will not cache if a particular instance is set to use password or
login privacy.

At this point, your entire website will now be cached efficiently. However, if you need more fine-grained control, see :doc:`cache_control`.
