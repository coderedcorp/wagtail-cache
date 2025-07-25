Usage
=====

In the Wagtail admin
--------------------

After installation, the cache is automatically turned on and in use. A new
settings panel is available in the Wagtail admin under **Settings > Cache**.
This panel shows cache information and also has a button to manually purge the
entire cache.


Clearing the cache manually
---------------------------

A utility function is provided to manually clear the cache. This will purge the
entire cache backend in use by ``WAGTAIL_CACHE_BACKEND``

.. code-block:: python

    from wagtailcache.cache import clear_cache

    # Clear the cache manually
    clear_cache()

There is also a Django management command to clear the cache:

.. code-block:: console

    $ python manage.py clear_wagtail_cache


Clearing the cache automatically
--------------------------------

In some scenarios, it may be ideal to automatically clear the cache after
publishing a page. To accomplish this, use a Wagtail hook as so

.. code-block:: python

    from wagtailcache.cache import clear_cache

    @hooks.register('after_create_page')
    @hooks.register('after_edit_page')
    def clear_wagtailcache(request, page):
        if page.live:
            clear_cache()


.. _purge_specific_urls:

Purge specific URLs
-------------------

Requires ``WAGTAIL_CACHE_KEYRING=True``

Sometimes you only want to delete specific pages in the cache automatically
after publishing a page. To achieve this, use a Wagtail hook as follows

Only this exact URL is used as a key

.. code-block:: python

    from wagtailcache.cache import clear_cache

    @hooks.register("after_create_page")
    @hooks.register("after_edit_page")
    def clear_wagtailcache(request, page):
        if page.live:
            clear_cache(
                [
                    page.full_url,  # page
                    page.get_parent().full_url,  # category page
                    page.get_url_parts()[1],  # root page
                ]
            )

Or we use regular expressions. Now all specific URLs are matched, even those
with GET parameters

.. code-block:: python

    from wagtailcache.cache import clear_cache

    @hooks.register("after_create_page")
    @hooks.register("after_edit_page")
    def clear_wagtailcache(request, page):
        if page.live:
            clear_cache(
                [
                    page.full_url + "(?:\?|$)",  # page
                    page.get_parent().full_url + "(?:\?|$)",  # category page
                    page.get_url_parts()[1] + "(?:\?|$)",  # root page
                ]
            )
