Supported Cache Backends
========================

Built-in Django cache backends
------------------------------

* **Memcached** (``django.core.cache.backends.memcached.MemcachedCache``) - untested, but should be working.
* **Redis** (``django.core.cache.backends.redis.RedisCache``) (New in Django 4.0) - tested, working.
* **Database** (``django.core.cache.backends.db.DatabaseCache``) - tested, working.
* **Filesystem** (``django.core.cache.backends.filebased.FileBasedCache``) - tested, working.
* **Local memory** (``django.core.cache.backends.locmem.LocMemCache``) - tested, working.
  But not ideal for production (see `Django docs for reasons why
  <https://docs.djangoproject.com/en/2.1/topics/cache/#local-memory-caching>`_).

.. note::
    Wagtail Cache may or may not work correctly with 3rd party backends. If you experience an issue, please
    `report it on our GitHub page <https://github.com/coderedcorp/wagtail-cache/issues>`_.

.. note::
    If you are currently using Redis or have other code that uses a Redis cache, It is advised to use
    separate cache definitions for wagtail-cache and your other uses.
