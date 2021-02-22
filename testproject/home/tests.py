from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings, modify_settings
from django.urls import reverse
from django.contrib.auth.models import User
from wagtailcache.settings import wagtailcache_settings
from wagtailcache.cache import CacheControl, Status, clear_cache
from wagtail.core import hooks
from wagtail.core.models import PageViewRestriction

from home.models import (
    CachedPage,
    CacheControlPage,
    CallableCacheControlPage,
    WagtailPage,
)


def hook_true(obj, is_cacheable: bool) -> bool:
    return True


def hook_false(obj, is_cacheable: bool) -> bool:
    return False


def hook_any(obj, is_cacheable: bool):
    return obj


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
            cls.page_callablecachecontrolpage,
        ]

    @classmethod
    def tearDownClass(cls):
        # Delete view restriction.
        cls.view_restriction.delete()
        # Delete pages.
        cls.page_cachedpage.delete()
        cls.page_cachecontrolpage.delete()
        cls.page_callablecachecontrolpage.delete()
        # Delete user.
        cls.user.delete()

    def tearDown(self):
        # Clear the cache and log out between each test.
        clear_cache()
        self.client.logout()
        # Delete any hooks.
        try:
            del hooks._hooks["is_request_cacheable"]
        except KeyError:
            pass
        try:
            del hooks._hooks["is_response_cacheable"]
        except KeyError:
            pass

    # --- UTILITIES ------------------------------------------------------------

    def get_hit(self, url: str):
        """
        Gets a page and tests that it was served from the cache.
        """
        # HEAD
        response = self.client.head(url)
        self.assertEqual(response.get(self.header_name, None), Status.HIT.value)
        # GET
        response = self.client.get(url)
        self.assertEqual(response.get(self.header_name, None), Status.HIT.value)
        return response

    def get_miss(self, url: str):
        """
        Gets a page and tests that it was not served from the cache.
        """
        # HEAD
        response = self.client.head(url)
        self.assertEqual(response.get(self.header_name, None), Status.MISS.value)
        # GET
        response = self.client.get(url)
        self.assertEqual(response.get(self.header_name, None), Status.MISS.value)
        return response

    def get_skip(self, url: str):
        """
        Gets a page and tests that it was intentionally not served from
        the cache.
        """
        # HEAD
        response = self.client.head(url)
        self.assertEqual(response.get(self.header_name, None), Status.SKIP.value)
        self.assertTrue(
            CacheControl.NOCACHE.value in response.get("Cache-Control", "")
            or CacheControl.PRIVATE.value in response.get("Cache-Control", "")
        )
        # GET
        response = self.client.get(url)
        self.assertEqual(response.get(self.header_name, None), Status.SKIP.value)
        self.assertTrue(
            CacheControl.NOCACHE.value in response.get("Cache-Control", "")
            or CacheControl.PRIVATE.value in response.get("Cache-Control", "")
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
            self.view_restriction.id,
            self.page_cachedpage_restricted.id,
        )
        response = self.client.post(
            auth_url,
            {
                "password": "the cybers",
                "return_url": self.page_cachedpage_restricted.get_url(),
            },
        )
        self.assertRedirects(response, self.page_cachedpage_restricted.get_url())
        # First get should skip cache, and also be set to private.
        response = self.get_skip(self.page_cachedpage_restricted.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get("Cache-Control", None), CacheControl.PRIVATE.value
        )
        # Second get should continue to skip and also be set to private.
        response = self.get_skip(self.page_cachedpage_restricted.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get("Cache-Control", None), CacheControl.PRIVATE.value
        )

    def test_page_404(self):
        # 404s should also be cached.
        self.get_miss("/gimme-a-404/")
        self.get_hit("/gimme-a-404/")

    @modify_settings(
        MIDDLEWARE={
            "remove": "django.contrib.auth.middleware.AuthenticationMiddleware",  # noqa
        }
    )
    def test_page_miss_without_auth(self):
        self.test_page_miss()

    @modify_settings(
        MIDDLEWARE={
            "remove": "django.contrib.auth.middleware.AuthenticationMiddleware",  # noqa
        }
    )
    def test_page_hit_without_auth(self):
        self.test_page_hit()

    @modify_settings(
        MIDDLEWARE={
            "remove": "django.contrib.auth.middleware.AuthenticationMiddleware",  # noqa
        }
    )
    def test_page_skip_without_auth(self):
        self.test_page_skip()

    @modify_settings(
        MIDDLEWARE={
            "remove": "django.contrib.auth.middleware.AuthenticationMiddleware",  # noqa
        }
    )
    def test_page_restricted_without_auth(self):
        self.test_page_restricted()

    @modify_settings(
        MIDDLEWARE={
            "remove": "django.contrib.auth.middleware.AuthenticationMiddleware",  # noqa
        }
    )
    def test_page_404_without_auth(self):
        self.test_page_404()

    # ---- TEST VIEWS ----------------------------------------------------------
    # Views use the decorators and should work without the middleware.

    @modify_settings(
        MIDDLEWARE={
            "remove": "wagtailcache.cache.UpdateCacheMiddleware",  # noqa
            "remove": "wagtailcache.cache.FetchFromCacheMiddleware",  # noqa
        }
    )
    def test_view_miss(self):
        # First get should miss cache.
        self.get_miss(reverse("cached_view"))

    @modify_settings(
        MIDDLEWARE={
            "remove": "wagtailcache.cache.UpdateCacheMiddleware",  # noqa
            "remove": "wagtailcache.cache.FetchFromCacheMiddleware",  # noqa
        }
    )
    def test_view_hit(self):
        # First get should miss cache.
        self.get_miss(reverse("cached_view"))
        # Second get should hit cache.
        self.get_hit(reverse("cached_view"))

    @modify_settings(
        MIDDLEWARE={
            "remove": "wagtailcache.cache.UpdateCacheMiddleware",  # noqa
            "remove": "wagtailcache.cache.FetchFromCacheMiddleware",  # noqa
        }
    )
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

    # ---- HOOKS ---------------------------------------------------------------

    def test_request_hook_true(self):
        # A POST should never be cached.
        response = self.client.post(reverse("cached_view"))
        self.assertEqual(response.get(self.header_name, None), Status.SKIP.value)
        response = self.client.post(reverse("cached_view"))
        self.assertEqual(response.get(self.header_name, None), Status.SKIP.value)
        # Register hook and assert it was actually registered.
        hooks.register("is_request_cacheable", hook_true)
        hook_fns = hooks.get_hooks("is_request_cacheable")
        self.assertEqual(hook_fns, [hook_true])
        # Setting `is_request_cacheale=True` does not really do much, because the
        # response still has the final say in whether or not the response is cached.
        # The no-cache page will still not be cached due to the response.
        # However a simple POST request will now be checked against the cache,
        # although once again, it will probably not get cached due to the response.
        response = self.client.post(reverse("cached_view"))
        self.assertEqual(response.get(self.header_name, None), Status.MISS.value)
        response = self.client.post(reverse("cached_view"))
        self.assertEqual(response.get(self.header_name, None), Status.MISS.value)

    def test_request_hook_false(self):
        # Register hook and assert it was actually registered.
        hooks.register("is_request_cacheable", hook_false)
        hook_fns = hooks.get_hooks("is_request_cacheable")
        self.assertEqual(hook_fns, [hook_false])
        # The cached page should be force skipped due to the hook returning false.
        self.get_skip(self.page_cachedpage.get_url())
        self.get_skip(self.page_cachedpage.get_url())

    def test_request_hook_any(self):
        # Register hook and assert it was actually registered.
        hooks.register("is_request_cacheable", hook_any)
        hook_fns = hooks.get_hooks("is_request_cacheable")
        self.assertEqual(hook_fns, [hook_any])
        # The page should be cached normally due to hook returning garbage.
        self.test_page_hit()

    def test_response_hook_true(self):
        # Register hook and assert it was actually registered.
        hooks.register("is_response_cacheable", hook_true)
        hook_fns = hooks.get_hooks("is_response_cacheable")
        self.assertEqual(hook_fns, [hook_true])
        # The no-cache page should be force cached due to the hook returning true.
        self.get_miss(self.page_cachecontrolpage.get_url())
        self.get_hit(self.page_cachecontrolpage.get_url())

    def test_response_hook_false(self):
        # Register hook and assert it was actually registered.
        hooks.register("is_response_cacheable", hook_false)
        hook_fns = hooks.get_hooks("is_response_cacheable")
        self.assertEqual(hook_fns, [hook_false])
        # The cached page should be force skipped due to the hook returning false.
        self.get_skip(self.page_cachedpage.get_url())
        self.get_skip(self.page_cachedpage.get_url())

    def test_response_hook_any(self):
        # Register hook and assert it was actually registered.
        hooks.register("is_response_cacheable", hook_any)
        hook_fns = hooks.get_hooks("is_response_cacheable")
        self.assertEqual(hook_fns, [hook_any])
        # The page should be cached normally due to hook returning garbage.
        self.test_page_hit()
