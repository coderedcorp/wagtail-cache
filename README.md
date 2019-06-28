# Wagtail Cache
A simple page cache for Wagtail based on the Django cache middleware.

[Documentation](https://docs.coderedcorp.com/wagtail-cache/) |
[Source code on GitHub](https://github.com/coderedcorp/wagtail-cache)

![PyPI - Downloads](https://img.shields.io/pypi/dm/wagtail-cache.svg)
![PyPI](https://img.shields.io/pypi/v/wagtail-cache.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wagtail-cache.svg)
![PyPI - Django Version](https://img.shields.io/pypi/djversions/wagtail-cache.svg)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/wagtail-cache.svg)

```
pip install wagtail-cache
```

## Why Wagtail Cache?
Django has a robust cache middleware that already has the functionality
needed to cache web pages effectively. But turning the cache middleware
on will blindly cache every request and does not work well with a wagtail site.

Wagtail Cache provides a decorator that works well with wagtail pages to
appropriately cache and serve them similar to Django's cache middleware.

The end result is ultra-fast page serving that requires zero database hits
to serve cached pages. Other solutions such as template caching still require
database hits for wagtail to serve a page.

## Notes
This cache feature was originally part of [coderedcms](https://github.com/coderedcorp/coderedcms)
and has been split out into this separate package. Wagtail Cache is
tried and tested, and is in use successfully on many live production sites.
