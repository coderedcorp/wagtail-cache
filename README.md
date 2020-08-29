Wagtail Cache
=============

A simple page cache for Wagtail based on the Django cache middleware.

[Documentation](https://docs.coderedcorp.com/wagtail-cache/) |
[Source code on GitHub](https://github.com/coderedcorp/wagtail-cache)


Status
------

|                        |                      |
|------------------------|----------------------|
| Python Package         | [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wagtail-cache)](https://pypi.org/project/wagtail-cache/) [![PyPI - Django Version](https://img.shields.io/pypi/djversions/wagtail-cache)](https://pypi.org/project/wagtail-cache/) [![PyPI - Wheel](https://img.shields.io/pypi/wheel/wagtail-cache)](https://pypi.org/project/wagtail-cache/) [![PyPI - Downloads](https://img.shields.io/pypi/dm/wagtail-cache)](https://pypi.org/project/wagtail-cache/) [![PyPI](https://img.shields.io/pypi/v/wagtail-cache)](https://pypi.org/project/wagtail-cache/) |
| Build                  | [![Build Status](https://dev.azure.com/coderedcorp/cr-github/_apis/build/status/cr-github?branchName=main)](https://dev.azure.com/coderedcorp/cr-github/_build/latest?definitionId=9&branchName=main) [![Azure DevOps tests (branch)](https://img.shields.io/azure-devops/tests/coderedcorp/cr-github/9/main)](https://dev.azure.com/coderedcorp/cr-github/_build/latest?definitionId=9&branchName=main) [![Azure DevOps coverage (branch)](https://img.shields.io/azure-devops/coverage/coderedcorp/cr-github/9/main)](https://dev.azure.com/coderedcorp/cr-github/_build/latest?definitionId=9&branchName=main) |


Quick Start
-----------

Follow the [Installation Guide](https://docs.coderedcorp.com/wagtail-cache/stable/getting_started/install.html)


Why Wagtail Cache?
------------------

Django has a robust cache middleware that already has the functionality
needed to cache web pages effectively. But turning the cache middleware
on will blindly cache every request and does not work well with a wagtail site.

Wagtail Cache provides a decorator that works well with wagtail pages to
appropriately cache and serve them similar to Django's cache middleware.

The end result is ultra-fast page serving that requires zero database hits
to serve cached pages. Other solutions such as template caching still require
database hits for wagtail to serve a page.


Contributing
------------

To set up your development environment:

1. Create a new environment:

```
python -m venv ~/Envs/wagtail-cache
# Mac and Linux
source ~/Envs/wagtail-cache/bin/activate
# Windows (PowerShell)
~/Envs/wagtail-cache/Scripts/Activate.ps1
```

2. Enter the source code directory and install the package locally with
   additional development tools:

```
pip install -r requirements-dev.txt
```

3. Write some code.

4. Next, run the static analysis tools (`flake8` and `mypy`)

```
flake8 ./wagtailcache/
mypy ./wagtailcache/
```

5. Next, run the units tests. A simple Wagtail project using Wagtail Cache is
   in the `testproject/` directory. The tests will generate a visual HTML file
   at `htmlcov/index.html` when finished, which you can open in your browser.
```
pytest ./testproject/
```

6. To build the documentation, run the following, which will output to the
   `docs/_build/html/` directory.
```
sphinx-build -M html ./docs/ ./docs/_build/ -W
```

7. To create a python package, run the following, which will output the package
   to the `dist/` directory.
```
python setup.py sdist bdist_wheel
```
