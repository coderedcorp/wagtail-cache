from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from wagtailcache.settings import get_config
from wagtailcache.cache import clear_cache

from home.models import (
    CachedPage, CacheControlPage, CallableCacheControlPage,
    WagtailPage,
)


class WagtailCacheTest(TestCase):
    def get_content_type(self, modelname: str):
        ctype, _ = ContentType.objects.get_or_create(model=modelname, app_label="home")
        return ctype

    def setUp(self):
        self.header_name = get_config()["WAGTAIL_CACHE_HEADER"]
        # Create some pages.
        self.page_cachedpage = CachedPage(
            title="CachedPage",
            slug="cachedpage",
            content_type=self.get_content_type("cachedpage"),
        )
        self.page_cachecontrolpage = CacheControlPage(
            title="CacheControlPage",
            slug="cachecontrolpage",
            content_type=self.get_content_type("cachecontrolpage"),
        )
        self.page_callablecachecontrolpage = CallableCacheControlPage(
            title="CachedPage",
            slug="callablecachecontrolpage",
            content_type=self.get_content_type("callablecachecontrolpage"),
        )
        self.page_wagtailpage = WagtailPage.objects.get(slug="home")
        self.page_wagtailpage.add_child(instance=self.page_cachedpage)
        self.page_wagtailpage.add_child(instance=self.page_cachecontrolpage)
        self.page_wagtailpage.add_child(instance=self.page_callablecachecontrolpage)

        self.should_cache_pages = [
            self.page_wagtailpage,
            self.page_cachedpage,
        ]
        self.skip_cache_pages = [
            self.page_cachecontrolpage,
            self.page_callablecachecontrolpage
        ]

    def tearDown(self):
        # Clear the cache between each test.
        clear_cache()
        # Delete pages.
        self.page_cachedpage.delete()
        self.page_cachecontrolpage.delete()
        self.page_callablecachecontrolpage.delete()

    def test_page_miss(self):
        for page in self.should_cache_pages:
            # First get should miss cache.
            response = self.client.get(page.get_url())
            self.assertEqual(response[self.header_name], "miss")

    def test_page_hit(self):
        for page in self.should_cache_pages:
            # First get should miss cache.
            response = self.client.get(page.get_url())
            self.assertEqual(response[self.header_name], "miss")
            # Second get should hit cache.
            response = self.client.get(page.get_url())
            self.assertEqual(response[self.header_name], "hit")

    def test_page_skip(self):
        for page in self.skip_cache_pages:
            # First get should skip cache.
            response = self.client.get(page.get_url())
            self.assertEqual(response[self.header_name], "skip")
            # Second get should continue to skip.
            response = self.client.get(page.get_url())
            self.assertEqual(response[self.header_name], "skip")

    def test_view_miss(self):
        # First get should miss cache.
        response = self.client.get(reverse("cached_view"))
        self.assertEqual(response[self.header_name], "miss")

    def test_view_hit(self):
        # First get should miss cache.
        response = self.client.get(reverse("cached_view"))
        self.assertEqual(response[self.header_name], "miss")
        # Second get should hit cache.
        response = self.client.get(reverse("cached_view"))
        self.assertEqual(response[self.header_name], "hit")

    def test_view_skip(self):
        # First get should skip cache.
        response = self.client.get(reverse("nocached_view"))
        self.assertEqual(response[self.header_name], "skip")
        # Second get should continue to skip.
        response = self.client.get(reverse("nocached_view"))
        self.assertEqual(response[self.header_name], "skip")
