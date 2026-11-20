Wagtail Cache
=============

A fast and simple page cache for Wagtail, inspired by the Django cache
middleware.

[Documentation](https://docs.coderedcorp.com/wagtail-cache/) |
[GitHub](https://github.com/coderedcorp/wagtail-cache) |
[PyPI](https://pypi.org/project/wagtail-cache/) |
[Release notes](https://docs.coderedcorp.com/wagtail-cache/releases.html)


Status
------

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wagtail-cache)](https://pypi.org/project/wagtail-cache/)
![PyPI - Wagtail Versions](https://img.shields.io/pypi/frameworkversions/wagtail/wagtail-cache)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/wagtail-cache)](https://pypi.org/project/wagtail-cache/)
[![PyPI](https://img.shields.io/pypi/v/wagtail-cache)](https://pypi.org/project/wagtail-cache/)


Quick Start
-----------

Follow the [Installation Guide](https://docs.coderedcorp.com/wagtail-cache/stable/getting_started/install.html)


Why Wagtail Cache?
------------------

Django has a robust cache middleware that already has the functionality
needed to cache web pages effectively. But turning the cache middleware
on will blindly cache every request and does not work well with a Wagtail site.

Wagtail Cache provides a middleware, decorator, and mixin that works well with
Wagtail pages, Django views, or even manually on any request/response to
efficiently cache and serve from cache.

The end result is ultra-fast page serving that requires zero database hits
to serve cached pages. Other solutions such as template caching still require
database hits for Wagtail to serve a page.

Wagtail Cache also does not require any additional infrastructure such as Redis,
Memcached, proxies, etc. It can work directly off the filesystem, or using any
of Django's built-in cache backends.


Contributing
------------

Follow the [contributing guide](https://docs.coderedcorp.com/wagtail-cache/stable/contributing.html)


Attribution
-----------

Icon file "wagtailcache-bolt.svg":

* Was sourced from the Fork Awesome project at
   https://github.com/ForkAwesome/Fork-Awesome.

* Is licensed under the Creative Commons Attribution 3.0 Unported license,
   a copy of which is available at https://creativecommons.org/licenses/by/3.0/

* Has been modified from the original sources.
