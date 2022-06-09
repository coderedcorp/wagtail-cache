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
adding the Wagtail Cache middleware.


2. Define a cache
-----------------

Next a cache must be configured in the settings. If you use redis, see :doc:`Supported Cache Backends </getting_started/supported_backends>`. Here is an example file cache,
which is suitable for use on any web server:

.. code-block:: python

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': os.path.join(BASE_DIR, 'cache'),
            'KEY_PREFIX': 'wagtailcache',
            'TIMEOUT': 3600, # one hour (in seconds)
        }
    }


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
login privacy. The ``WagtailCacheMixin`` also gives you the option to add a
custom Cache-Control header via ``cache_control``, which can be a dynamic
function or a string:

.. code-block:: python

    from wagtailcache.cache import WagtailCacheMixin

    class MyPage(WagtailCacheMixin, Page):

        cache_control = 'no-cache'

        ...


Setting this to contain ``no-cache`` or ``private`` will tell wagtail-cache
**not** to cache this page. You could also set it to a custom value such as
"public, max-age=3600". It can also be a function:

.. code-block:: python

    from wagtailcache.cache import WagtailCacheMixin

    class MyPage(WagtailCacheMixin, Page):

        def cache_control(self):
            return 'no-cache'

        ...

Regardless of the mixin, Wagtail Cache will never cache a response that has a
``Cache-Control`` header containing ``no-cache`` or ``private``. Adding this
header to any response will cause it to be skipped.

To explicitly not cache certain views or URL patterns, you could also wrap them
with the ``nocache_page`` decorator, which adds the ``Cache-Control: no-cache``
header to all responses of that view or URL pattern. To use with a view:

.. code-block:: python

    from wagtailcache.cache import nocache_page

    @nocache_page
    def myview(request):
        ...

Or on a URL pattern:

.. code-block:: python

    from wagtailcache.cache import nocache_page

    ...

    url(r'^url/pattern/$', nocache_page(viewname), name='viewname'),

    ...

When using the Wagtail Cache middleware, the middleware will detect CSRF tokens and will only cache
those responses on a per-cookie basis. So Wagtail Cache should work well with CSRF tokens 🙂.
But if you still experience issues with CSRF tokens, use the mixin, the ``nocache_page`` decorator,
or set the ``Cache-Control`` header to ``no-cache`` on the response to guarantee that it will
never be cached. If you are using the ``cache_page`` decorator instead of the middleware, you
**must** use the mixin or set the ``Cache-Control`` header on responses with CSRF tokens to avoid
getting 403 forbidden errors.


Using a separate cache backend
------------------------------

For complex sites, it may be desirable to use a separate cache backend only for
the page cache, so that purging the page cache will not affect other caches:

.. code-block:: python

    WAGTAIL_CACHE_BACKEND = 'pagecache'

    CACHES = {
        'default': {
            ...
        },
        'pagecache': {
            ...
        }
    }


Only cache specific views
-------------------------

The wagtail-cache middleware will attempt to cache ALL responses that appear to be cacheable
(meaning the response does not contain a 'no-cache'/'private' Cache-Control header, the request method
is GET or HEAD, the response status code is 200, 301, 302, 404, the response did not set a cookie,
the page is not in preview mode, a user is not logged in, and many other requirements).

To only cache specific views, remove the middleware and use the ``cache_page`` decorator on views or URLs.

Alternatively, to continue using the middleware but explicitly not cache certain views or URLs, wrap those
views or URLs with the ``nocache_page`` decorator.

Note that when using the ``cache_page`` decorator, it is not possible to cache Wagtail page 404s or redirects. Only the
middleware is able to cache those responses.

Caching wagtail pages only
~~~~~~~~~~~~~~~~~~~~~~~~~~

Most likely you will want this on all of your wagtail pages, so you will have to
replace the inclusion of ``wagtail_urls`` in your project's ``urls.py``. You
will need to change from this:

.. code-block:: python

    from django.conf.urls import url

    url(r'', include(wagtail_urls)),

To this:

.. code-block:: python

    from django.conf.urls import url

    from django.contrib.auth import views as auth_views
    from wagtail.core.urls import serve_pattern, WAGTAIL_FRONTEND_LOGIN_TEMPLATE
    from wagtail.core import views as wagtail_views
    from wagtailcache.cache import cache_page

    # Copied from wagtail.core.urls:
    url(r'^_util/authenticate_with_password/(\d+)/(\d+)/$', wagtail_views.authenticate_with_password,
        name='wagtailcore_authenticate_with_password'),
    url(r'^_util/login/$', auth_views.LoginView.as_view(template_name=WAGTAIL_FRONTEND_LOGIN_TEMPLATE),
        name='wagtailcore_login'),

    # Wrap the serve function with wagtail-cache
    url(serve_pattern, cache_page(wagtail_views.serve), name='wagtail_serve'),

Caching specific wagtail page models only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also use the decorator on specific wagtail pages. It is helpful in
Wagtail sites where the requirement is not to cache all pages:

.. code-block:: python

    from django.utils.decorators import method_decorator
    from wagtailcache.cache import cache_page, WagtailCacheMixin

    @method_decorator(cache_page, name='serve')
    class MyPage(WagtailCacheMixin, Page):
        ...

Caching views
~~~~~~~~~~~~~

You can also use the decorator on views:

.. code-block:: python

    from wagtailcache.cache import cache_page

    @cache_page
    def myview(request):
        ...

To use it on class-based views:

.. code-block:: python

    from django.utils.decorators import method_decorator
    from wagtailcache.cache import cache_page

    @method_decorator(cache_page, name='dispatch')
    class MyView(TemplateView):
        ...
