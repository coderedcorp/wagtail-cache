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

Finally, use the ``cache_page`` decorator on any views or URLs. Most likely you will want this on
all of your wagtail pages, so you will have to replace the ``wagtail_urls`` with the following
in your project's urls.py::

    from django.conf.urls import url

    # Replace:
    # url(r'', include(wagtail_urls)),

    # With:

    from django.contrib.auth import views as auth_views
    from wagtail.core.urls import serve_pattern, WAGTAIL_FRONTEND_LOGIN_TEMPLATE
    from wagtail.core import views as wagtail_views
    from wagtailcache.cache import cache_page

    # Direct copy of wagtail.core.urls
    url(r'^_util/authenticate_with_password/(\d+)/(\d+)/$', wagtail_views.authenticate_with_password,
        name='wagtailcore_authenticate_with_password'),
    url(r'^_util/login/$', auth_views.login, {'template_name': WAGTAIL_FRONTEND_LOGIN_TEMPLATE},
        name='wagtailcore_login'),

    # Wrap the serve function with wagtail-cache
    url(serve_pattern, cache_page(wagtail_views.serve), name='wagtail_serve'),

You can also use the decorator on views::

    from wagtailcache.cache import cache_page

    @cache_page
    def myview(request):
        ...


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
