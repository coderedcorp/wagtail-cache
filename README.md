# Wagtail Cache
A simple page cache for Wagtail using the Django cache middleware.

[Documentation](https://docs.coderedcorp.com/wagtail-cache/) |
[Source code on GitHub](https://github.com/coderedcorp/wagtail-cache)

```
pip install wagtail-cache
```

## Why Wagtail Cache?
Django has a robust cache middleware that already has the functionality
needed to cache web pages effectively. But turning the cache middleware
on will blindly cache every request and does not work well with a wagtail site.

Wagtail Cache provides a decorator that works well with wagtail pages to
appropriately cache and serve them using Django's cache middleware.

The end result is ultra-fast page serving that requires zero database hits
to serve cached pages. Other solutions such as template caching still require
database hits for wagtail to serve a page.

## Notes
This cache feature was originally part of [coderedcms](https://github.com/coderedcorp/coderedcms)
and has been in use successfully on live production sites. Eventually the
coderedcms cache will be replaced with wagtail-cache after it has been tested.
