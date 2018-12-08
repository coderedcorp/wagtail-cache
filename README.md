# wagtail-cache
A simple page cache for Wagtail using the Django cache middleware.


## Installation
```
pip install https://github.com/coderedcorp/wagtail-cache/archive/master.zip
```

Add to installed apps in the project settings:
```
INSTALLED_APPS = [
    ...
    wagtailcache,
    ...
]
```

Next a cache must be configured in the settings. The default cache used is `default`, but this can be changed with the `WAGTAIL_CACHE_BACKEND` setting. Here is an example file cache, which is suitable for use on a single web server:
```
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'cache'),
        'KEY_PREFIX': 'wagtailcache',
        'TIMEOUT': 3600, # one hour (in seconds)
    }
}
```

Or to use a separate cache backend:
```
WAGTAIL_CACHE_BACKEND = 'pagecache'

CACHES = {
    'default': {
        ...
    },
    'pagecache': {
        ...
    }
}
```

Finally, use the `cache_page` decorator on any views or URLs. Most likely you will want this on all of your wagtail pages, so you will have to replace the `wagtail_urls` with the following in your project's urls.py

```
from django.conf.urls import url

# Replace wagtail_urls:
# url(r'', include(wagtail_urls)),

# With the following:

from django.contrib.auth import views as auth_views
from wagtail.core.urls import serve_pattern, WAGTAIL_FRONTEND_LOGIN_TEMPLATE
from wagtail.core import views as wagtail_views
from wagtailcache import cache_page

# Direct copy of wagtail.core.urls
url(r'^_util/authenticate_with_password/(\d+)/(\d+)/$', wagtail_views.authenticate_with_password,
    name='wagtailcore_authenticate_with_password'),
url(r'^_util/login/$', auth_views.login, {'template_name': WAGTAIL_FRONTEND_LOGIN_TEMPLATE},
    name='wagtailcore_login'),

# Wrap the serve function with wagtail-cache
url(serve_pattern, cache_page(wagtail_views.serve), name='wagtail_serve'),
```

Or you can use the decorator on a view:
```
from wagtailcache import cache_page

@cache_page
def myview(request):
    ...
```


## Usage
After installation, the cache is automatically turned on and in use. A new settings panel is available in the wagtail admin under Settings > Cache. This panel shows cache information and also has a button to manually purge the entire cache.


## Clearing the cache automatically
In some scenarios, it may be ideal to automatically clear the cache after publishing a page. To accomplish this, use a wagtail hook as so:
```
from wagtailcache import clear_cache

@hooks.register('after_create_page')
@hooks.register('after_edit_page')
def clear_wagtailcache(request, page):
    if page.live:
        clear_cache()
```


## Settings

### WAGTAIL_CACHE
Boolean toggling whether or not to load the page caching machinery and enable cache settings in the wagtail admin. Defaults to `True` which is on. Most developers will want to set this to `False` in the development environment.

### WAGTAIL_CACHE_BACKEND
The name of the django cache alias/backend to use for the page cache. Defaults to `'default'` which is required by Django when using the cache. Complex projects would likely want to use a separate cache for the page cache to easily purge as needed without affecting other caches. Clearing the cache through the wagtail admin will purge this entire cache.

### WAGTAIL_CACHE_HEADER
By default, an HTTP header called `X-Wagtail-Cache` is added to the response to indicate a cache hit or miss. To turn off this header, set WAGTAIL_CACHE_HEADER = `False`, or to customize the header set to a string. Note that other HTTP headers may also added by the Django cache middleware.


## Hooks

### `is_request_cacheable`
The callable passed into this hook should take a `request` argument, and return a `bool` indicating whether or not the response to this request should be cached (served from the cache if it is already cached, or added to the cache if it is not already cached). Not returning, or returning anything other than a bool will not affect the caching decision. For example:
```
from wagtail.core import hooks

@hooks.register('is_request_cacheable')
def nocache_in_query(request):
    # if the querystring contains a "nocache" key, return False to forcibly not cache.
    # otherwise, do not return to let wagtail-cache decide how to cache.
    if 'nocache' in request.GET:
        return False
```


## Notes
This cache feature was originally part of [coderedcms](https://github.com/coderedcorp/coderedcms) and has been in use successfully on live production sites. This is the first attempt at refactoring it into a separate package. Eventually the coderedcms cache will be replaced with wagtail-cache after it has been tested.

Once this project receives some initial community feedback and a round of bug fixes we will publish on pypi.

Requires Django >= 2.0 and Wagtail >= 2.0