Installation
============

1. Install
----------

::

    pip install wagtail-cache

Add to installed apps in the project settings::

    INSTALLED_APPS = [
        ...
        wagtailcache,
        ...
    ]


2. Define a cache
-----------------

Next a cache must be configured in the settings. Here is an example file cache, which is
suitable for use on any web server::

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': os.path.join(BASE_DIR, 'cache'),
            'KEY_PREFIX': 'wagtailcache',
            'TIMEOUT': 3600, # one hour (in seconds)
        }
    }


3. Use the cache decorator
--------------------------

Finally, use the ``cache_page`` decorator on any views or URLs.

Caching pages
~~~~~~~~~~~~~

Most likely you will want this on all of your wagtail pages, so you will have to
replace the inclusion of ``wagtail_urls`` in your project's ``urls.py``. You will
need to change from this::

    from django.conf.urls import url

    url(r'', include(wagtail_urls)),

To this::

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

Caching views
~~~~~~~~~~~~~

You can also use the decorator on views::

    from wagtailcache.cache import cache_page

    @cache_page
    def myview(request):
        ...

To use it on class-based views::

    from django.utils.decorators import method_decorator
    from wagtailcache.cache import cache_page

    @method_decorator(cache_page, name='dispatch')
    class MyView(TemplateView):
        ...


4. Instruct pages how to cache (optional)
-----------------------------------------

There are many situations where a specific page should not be cached. For example,
a page with privacy or view restrictions (e.g. password, login required), or possibly a form or
other page with CSRF data.

For that reason, it is recommended to add the ``WagtailCacheMixin`` to your Page models,
which will handle all of these situations and provide additional control over how and when
pages cache.

Add the mixin **to the beginning** of the class inheritance::

    from wagtailcache.cache import WagtailCacheMixin

    class MyPage(WagtailCacheMixin, Page):
        ...


Now ``MyPage`` will not cache if a particular instance is set to use password or login
privacy. The ``WagtailCacheMixin`` also gives you the option to add a custom Cache-Control
header via ``cache_control``, which can be a dynamic function or a string::

    from wagtailcache.cache import WagtailCacheMixin

    class MyPage(WagtailCacheMixin, Page):

        cache_control = 'no-cache'

        ...


Setting this to ``no-cache`` or ``private`` will tell wagtail-cache **not** to cache this page.
You could also set it to a custom value such as "public, max-age=3600". It can also be a function::

    from wagtailcache.cache import WagtailCacheMixin

    class MyPage(WagtailCacheMixin, Page):

        def cache_control(self):
            return 'no-cache'

        ...

Regardless of the mixin, wagtail-cache will never cache a response that has a ``Cache-Control`` header
containing ``no-cache`` or ``private``. Adding this header to any response will cause it to be skipped.


Using a separate cache backend
------------------------------

For complex sites, it may be desirable to use a separate cache backend only for the page cache,
so that purging the page cache will not affect other caches::

    WAGTAIL_CACHE_BACKEND = 'pagecache'

    CACHES = {
        'default': {
            ...
        },
        'pagecache': {
            ...
        }
    }
