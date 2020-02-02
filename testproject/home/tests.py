from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings, modify_settings
from django.urls import reverse
from django.contrib.auth.models import User
from wagtailcache.settings import wagtailcache_settings
from wagtailcache.cache import clear_cache
from wagtail.core.models import PageViewRestriction

from home.models import CachedPage, CacheControlPage, CallableCacheControlPage, WagtailPage


class WagtailCacheTest(TestCase):

    @classmethod
    def get_content_type(cls, modelname: str):
        ctype, _ = ContentType.objects.get_or_create(model=modelname, app_label="home")
        return ctype

    @classmethod
    def setUpClass(cls):
        cls.header_name = wagtailcache_settings.WAGTAIL_CACHE_HEADER
        # Create an admin user.
        cls.user = User.objects.create(
            username="admin",
            is_superuser=True,
        )
        # Create some pages.
        cls.page_cachedpage = CachedPage(
            title="CachedPage",
            slug="cachedpage",
            content_type=cls.get_content_type("cachedpage"),
        )
        cls.page_cachedpage_restricted = CachedPage(
            title="CachedPage",
            slug="cachedpage-restricted",
            content_type=cls.get_content_type("cachedpage"),
        )
        cls.page_cachecontrolpage = CacheControlPage(
            title="CacheControlPage",
            slug="cachecontrolpage",
            content_type=cls.get_content_type("cachecontrolpage"),
        )
        cls.page_callablecachecontrolpage = CallableCacheControlPage(
            title="CachedPage",
            slug="callablecachecontrolpage",
            content_type=cls.get_content_type("callablecachecontrolpage"),
        )
        cls.page_wagtailpage = WagtailPage.objects.get(slug="home")
        cls.page_wagtailpage.add_child(instance=cls.page_cachedpage)
        cls.page_wagtailpage.add_child(instance=cls.page_cachedpage_restricted)
        cls.page_wagtailpage.add_child(instance=cls.page_cachecontrolpage)
        cls.page_wagtailpage.add_child(instance=cls.page_callablecachecontrolpage)

        # Create the view restriction.
        cls.view_restriction = PageViewRestriction.objects.create(
            page=cls.page_cachedpage_restricted,
            restriction_type=PageViewRestriction.PASSWORD,
            password="the cybers",
        )

        # List of pages to test.
        cls.should_cache_pages = [
            cls.page_wagtailpage,
            cls.page_cachedpage,
        ]
        cls.skip_cache_pages = [
            cls.page_cachedpage_restricted,
            cls.page_cachecontrolpage,
            cls.page_callablecachecontrolpage
        ]

    @classmethod
    def tearDownClass(cls):
        # Delete pages.
        cls.page_cachedpage.delete()
        cls.page_cachecontrolpage.delete()
        cls.page_callablecachecontrolpage.delete()

    def tearDown(self):
        # Clear the cache and log out between each test.
        clear_cache()
        self.client.logout()

    # --- UTILITIES ------------------------------------------------------------

    def get_hit(self, url: str):
        """
        Gets a page and tests that it was served from the cache.
        """
        # HEAD
        response = self.client.head(url)
        self.assertEqual(response.get(self.header_name, None), "hit")
        # GET
        response = self.client.get(url)
        self.assertEqual(response.get(self.header_name, None), "hit")
        return response

    def get_miss(self, url: str):
        """
        Gets a page and tests that it was not served from the cache.
        """
        # HEAD
        response = self.client.head(url)
        self.assertEqual(response.get(self.header_name, None), "miss")
        # GET
        response = self.client.get(url)
        self.assertEqual(response.get(self.header_name, None), "miss")
        return response

    def get_skip(self, url: str):
        """
        Gets a page and tests that it was intentionally not served from
        the cache.
        """
        # HEAD
        response = self.client.head(url)
        self.assertEqual(response.get(self.header_name, None), "skip")
        self.assertTrue(
            "no-cache" in response.get("Cache-Control", "") or
            "private" in response.get("Cache-Control", "")
        )
        # GET
        response = self.client.get(url)
        self.assertEqual(response.get(self.header_name, None), "skip")
        self.assertTrue(
            "no-cache" in response.get("Cache-Control", "") or
            "private" in response.get("Cache-Control", "")
        )
        return response

    # ---- TEST PAGES ----------------------------------------------------------

    def test_page_miss(self):
        for page in self.should_cache_pages:
            self.get_miss(page.get_url())

    def test_page_hit(self):
        for page in self.should_cache_pages:
            # First get should miss cache.
            self.get_miss(page.get_url())
            # Second get should hit cache.
            self.get_hit(page.get_url())

    def test_page_skip(self):
        for page in self.skip_cache_pages:
            # First get should skip cache.
            self.get_skip(page.get_url())
            # Second get should continue to skip.
            self.get_skip(page.get_url())

    def test_page_restricted(self):
        auth_url = "/_util/authenticate_with_password/%d/%d/" % (
            self.view_restriction.id, self.page_cachedpage_restricted.id
        )
        response = self.client.post(auth_url, {
            "password": "the cybers",
            "return_url": self.page_cachedpage_restricted.get_url(),
        })
        self.assertRedirects(response, self.page_cachedpage_restricted.get_url())
        # First get should skip cache, and also be set to private.
        response = self.get_skip(self.page_cachedpage_restricted.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("Cache-Control", None), "private")
        # Second get should continue to skip and also be set to private.
        response = self.get_skip(self.page_cachedpage_restricted.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("Cache-Control", None), "private")

    # ---- TEST VIEWS ----------------------------------------------------------
    # Views use the decorators and should work without the middleware.

    @modify_settings(MIDDLEWARE={
        "remove": 'wagtailcache.cache.UpdateCacheMiddleware',  # noqa
        "remove": 'wagtailcache.cache.FetchFromCacheMiddleware',  # noqa
    })
    def test_view_miss(self):
        # First get should miss cache.
        self.get_miss(reverse("cached_view"))

    @modify_settings(MIDDLEWARE={
        "remove": 'wagtailcache.cache.UpdateCacheMiddleware',  # noqa
        "remove": 'wagtailcache.cache.FetchFromCacheMiddleware',  # noqa
    })
    def test_view_hit(self):
        # First get should miss cache.
        self.get_miss(reverse("cached_view"))
        # Second get should hit cache.
        self.get_hit(reverse("cached_view"))

    @modify_settings(MIDDLEWARE={
        "remove": 'wagtailcache.cache.UpdateCacheMiddleware',  # noqa
        "remove": 'wagtailcache.cache.FetchFromCacheMiddleware',  # noqa
    })
    def test_view_skip(self):
        # First get should skip cache.
        self.get_skip(reverse("nocached_view"))
        # Second get should continue to skip.
        self.get_skip(reverse("nocached_view"))

    # ---- ADMIN VIEWS ---------------------------------------------------------

    def test_admin(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("wagtailcache:index"))
        self.client.logout()
        self.assertEqual(response.status_code, 200)

    def test_admin_clearcache(self):
        # First get should miss cache.
        self.get_miss(self.page_cachedpage.get_url())
        # Second get should hit cache.
        self.get_hit(self.page_cachedpage.get_url())
        # Now log in as admin and clear the cache.
        self.client.force_login(self.user)
        response = self.client.get(reverse("wagtailcache:clearcache"))
        self.client.logout()
        self.assertEqual(response.status_code, 200)
        # Now the page should miss cache.
        self.get_miss(self.page_cachedpage.get_url())

    # ---- ALTERNATE SETTINGS --------------------------------------------------

    @override_settings(WAGTAIL_CACHE=True)
    def test_enable_wagtailcache(self):
        # Intentionally enable wagtail-cache, make sure it works.
        response = self.client.get(self.page_cachedpage.get_url())
        self.assertIsNotNone(response.get(self.header_name, None))

    @override_settings(WAGTAIL_CACHE=False)
    def test_disable_wagtailcache(self):
        # Intentionally disable wagtail-cache, make sure it is inactive.
        response = self.client.get(self.page_cachedpage.get_url())
        self.assertIsNone(response.get(self.header_name, None))

    @override_settings(WAGTAIL_CACHE_BACKEND="zero")
    def test_zero_timeout(self):
        # Wagtail-cache should ignore the page when a timeout is zero.
        response = self.client.get(self.page_cachedpage.get_url())
        self.assertIsNone(response.get(self.header_name, None))
        # Second should also not cache.
        response = self.client.get(self.page_cachedpage.get_url())
        self.assertIsNone(response.get(self.header_name, None))
        # Load admin panel to render the zero timeout.
        self.test_admin()
