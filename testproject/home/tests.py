import datetime
import time

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import caches
from django.test import modify_settings
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from wagtail import hooks
from wagtail.models import PageViewRestriction

from home.models import CacheControlPage
from home.models import CachedPage
from home.models import CallableCacheControlPage
from home.models import CookiePage
from home.models import CsrfPage
from home.models import WagtailPage
from wagtailcache.cache import CacheControl
from wagtailcache.cache import clear_cache
from wagtailcache.cache import Status
from wagtailcache.models import KeyringItem
from wagtailcache.settings import wagtailcache_settings
from wagtailcache.utils import batched


def hook_true(obj, is_cacheable: bool) -> bool:
    return True


def hook_false(obj, is_cacheable: bool) -> bool:
    return False


def hook_any(obj, is_cacheable: bool):
    return obj


class WagtailCacheTest(TestCase):
    @classmethod
    def get_content_type(cls, modelname: str):
        ctype, _ = ContentType.objects.get_or_create(
            model=modelname, app_label="home"
        )
        return ctype

    @classmethod
    def setUpClass(cls):
        cls.header_name = wagtailcache_settings.WAGTAIL_CACHE_HEADER
        cls.cache = caches[wagtailcache_settings.WAGTAIL_CACHE_BACKEND]
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
        cls.page_cookiepage = CookiePage(
            title="CookiePage",
            slug="cookiepage",
            content_type=cls.get_content_type("cookiepage"),
        )
        cls.page_csrfpage = CsrfPage(
            title="CsrfPage",
            slug="csrfpage",
            content_type=cls.get_content_type("csrfpage"),
        )
        cls.page_wagtailpage = WagtailPage.objects.get(slug="home")
        cls.page_wagtailpage.add_child(instance=cls.page_cachedpage)
        cls.page_wagtailpage.add_child(instance=cls.page_cachedpage_restricted)
        cls.page_wagtailpage.add_child(instance=cls.page_cachecontrolpage)
        cls.page_wagtailpage.add_child(
            instance=cls.page_callablecachecontrolpage
        )
        cls.page_wagtailpage.add_child(instance=cls.page_cookiepage)
        cls.page_wagtailpage.add_child(instance=cls.page_csrfpage)
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
        cls.page_cookiepage.delete()
        cls.page_csrfpage.delete()
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
    def head_hit(self, url: str):
        """
        HEAD a page and test that it was served from the cache.
        """
        response = self.client.head(url)
        self.assertEqual(response.get(self.header_name, None), Status.HIT.value)
        return response

    def get_hit(self, url: str):
        """
        Gets a page and tests that it was served from the cache.
        """
        response = self.client.get(url)
        self.assertEqual(response.get(self.header_name, None), Status.HIT.value)
        return response

    def head_miss(self, url: str):
        """
        HEAD a page and test that it was not served from the cache.
        """
        response = self.client.head(url)
        self.assertEqual(
            response.get(self.header_name, None), Status.MISS.value
        )

    def get_miss(self, url: str):
        """
        Gets a page and tests that it was not served from the cache.
        """
        response = self.client.get(url)
        self.assertEqual(
            response.get(self.header_name, None), Status.MISS.value
        )
        return response

    def head_skip(self, url: str):
        """
        HEAD a page and test that it was intentionally not served from the
        cache.
        """
        response = self.client.head(url)
        self.assertEqual(
            response.get(self.header_name, None), Status.SKIP.value
        )
        self.assertTrue(
            CacheControl.NOCACHE.value in response.get("Cache-Control", "")
            or CacheControl.PRIVATE.value in response.get("Cache-Control", "")
        )

    def get_skip(self, url: str):
        """
        Gets a page and tests that it was intentionally not served from
        the cache.
        """
        response = self.client.get(url)
        self.assertEqual(
            response.get(self.header_name, None), Status.SKIP.value
        )
        self.assertTrue(
            CacheControl.NOCACHE.value in response.get("Cache-Control", "")
            or CacheControl.PRIVATE.value in response.get("Cache-Control", "")
        )
        return response

    def post_skip(self, url: str):
        """
        POSTS a page and tests that it was intentionally not served from
        the cache.
        """
        response = self.client.post(url)
        self.assertEqual(
            response.get(self.header_name, None), Status.SKIP.value
        )
        self.assertTrue(
            CacheControl.NOCACHE.value in response.get("Cache-Control", "")
            or CacheControl.PRIVATE.value in response.get("Cache-Control", "")
        )
        return response

    # ---- TEST PAGES ----------------------------------------------------------
    def test_page_miss(self):
        for page in self.should_cache_pages:
            self.head_miss(page.get_url())
            self.get_miss(page.get_url())

    def test_page_hit(self):
        for page in self.should_cache_pages:
            # First get should miss cache.
            self.head_miss(page.get_url())
            self.get_miss(page.get_url())
            # Second get should hit cache.
            self.head_hit(page.get_url())
            self.get_hit(page.get_url())

    def test_page_skip(self):
        for page in self.skip_cache_pages:
            # First get should skip cache.
            self.head_skip(page.get_url())
            self.get_skip(page.get_url())
            # Second get should continue to skip.
            self.head_skip(page.get_url())
            self.get_skip(page.get_url())

    def test_page_post(self):
        # POSTs should never normally be cached, by default.
        for page in self.should_cache_pages:
            # First post should skip cache.
            self.post_skip(page.get_url())
            # Second post should skip cache.
            self.post_skip(page.get_url())

    def test_querystrings(self):
        for page in self.should_cache_pages:
            # First get should miss cache.
            self.head_miss(page.get_url())
            self.get_miss(page.get_url())
            # Second get should hit cache.
            self.head_hit(page.get_url())
            self.get_hit(page.get_url())
            # A get matching WAGTAIL_CACHE_IGNORE_QS should also hit the cache.
            self.head_hit(page.get_url() + "?utm_code=0")
            self.get_hit(page.get_url() + "?utm_code=0")
            # A get with non-ignored querystrings should miss.
            self.head_miss(page.get_url() + "?valid=0")
            self.get_miss(page.get_url() + "?valid=0")
            # A get with both should also hit, since it is the second request.
            self.head_hit(page.get_url() + "?valid=0&utm_code=0")
            self.get_hit(page.get_url() + "?valid=0&utm_code=0")

    @override_settings(WAGTAIL_CACHE_IGNORE_COOKIES=False)
    def test_cookie_page(self):
        # First request should skip, since the cookie is being set.
        self.get_skip(self.page_cookiepage.get_url())
        # Second request should miss, since this request contains a cookie.
        self.get_miss(self.page_cookiepage.get_url())
        # Third request should hit.
        self.get_hit(self.page_cookiepage.get_url())

    @override_settings(WAGTAIL_CACHE_IGNORE_COOKIES=True)
    def test_cookie_page_ignore(self):
        # With the setting turned on, it will strip all cookies (other than CSRF
        # or session id). Therefore, each response is going to SKIP due to
        # setting a cooking in response to a cookie-less request.
        # First request should skip, since the cookie is not yet set.
        self.get_skip(self.page_cookiepage.get_url())
        # Second request should continue to skip.
        self.get_skip(self.page_cookiepage.get_url())

    @override_settings(WAGTAIL_CACHE_IGNORE_COOKIES=False)
    def test_csrf_page(self):
        # First request should skip, since the CSRF token is being set.
        self.get_skip(self.page_csrfpage.get_url())
        # Second request should also miss, since this request now contains a
        # CSRF cookie.
        self.get_miss(self.page_csrfpage.get_url())
        # Third request should hit from the cache.
        self.get_hit(self.page_csrfpage.get_url())

    @override_settings(WAGTAIL_CACHE_IGNORE_COOKIES=True)
    def test_csrf_page_ignore(self):
        # This should behave exactly the same with or without the setting.
        # First request should skip, since the CSRF token is being set.
        self.get_skip(self.page_csrfpage.get_url())
        # Second request should also miss, since this request now contains a
        # CSRF cookie.
        self.get_miss(self.page_csrfpage.get_url())
        # Third request should hit from the cache.
        self.get_hit(self.page_csrfpage.get_url())

    @override_settings(WAGTAIL_CACHE_IGNORE_COOKIES=False)
    def test_client_tracking_cookies(self):
        # Normally, when a client sends a cookie, that is stored separately in
        # the cache due to presence of the ``Vary: Cookie`` header. This means
        # trackers that pollute the cookies effectively bust the cache. Under
        # normal behavior, these should in fact be cached separately.
        # A get should miss cache.
        self.get_miss(self.page_cachedpage.get_url())
        # A get with different cookies should also miss the cache.
        self.client.cookies["annoying_tracker"] = "we see all"
        self.get_miss(self.page_cachedpage.get_url())
        # A get with different cookies should also miss the cache.
        self.client.cookies["_dataminer"] = "precious data"
        self.get_miss(self.page_cachedpage.get_url())

    @override_settings(WAGTAIL_CACHE_IGNORE_COOKIES=True)
    def test_client_tracking_cookies_ignore(self):
        # Normally, when a client sends a cookie, that is stored separately in
        # the cache due to presence of the ``Vary: Cookie`` header. This means
        # trackers that pollute the cookies effectively bust the cache. Under
        # normal behavior, these should in fact be cached separately.
        # With this setting ``True``, all cookies other than Django session and
        # CSRF token should be ignored and continue to hit the cache.
        # A get should miss cache.
        self.get_miss(self.page_cachedpage.get_url())
        # A get with different cookies should hit.
        self.client.cookies["annoying_tracker"] = "we see all"
        self.get_hit(self.page_cachedpage.get_url())
        # A get with different cookies should also hit.
        self.client.cookies["_dataminer"] = "precious data"
        self.get_hit(self.page_cachedpage.get_url())

    @override_settings(WAGTAIL_CACHE_IGNORE_COOKIES=True)
    def test_vary_header_parse(self):
        self.get_miss(reverse("vary_view"))
        r = self.get_hit(reverse("vary_view"))
        # Cookie should have been stripped from the Vary header while preserving
        # case and order of the other items.
        self.assertEqual(r["Vary"], "A, B, C")

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
        self.assertRedirects(
            response, self.page_cachedpage_restricted.get_url()
        )
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

    def test_template_response_view_hit(self):
        # First get should miss cache.
        self.get_miss(reverse("template_response_view"))
        # Second get should hit cache.
        self.get_hit(reverse("template_response_view"))

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
        self.assertEqual(response.status_code, 302)
        # Now the page should miss cache.
        self.get_miss(self.page_cachedpage.get_url())

    # ---- PURGE SPECIFIC URLS & CLEAR ALL--------------------------------------
    def test_cache_keyring(self):
        # Check if keyring is not present
        self.assertEqual(KeyringItem.objects.count(), 0)
        # Get should hit cache.
        self.get_miss(self.page_cachedpage.get_url())
        self.assertEqual(KeyringItem.objects.count(), 1)
        # Get first key from keyring
        url = "http://%s%s" % ("testserver", self.page_cachedpage.get_url())
        keyring_item = KeyringItem.objects.active_for_url_regexes(url).first()
        # Compare Keys
        self.assertEqual(keyring_item.url, url)

    def test_clear_cache(self):
        # First get should miss cache.
        self.get_miss(self.page_cachedpage.get_url())
        # Second get should hit cache.
        self.get_hit(self.page_cachedpage.get_url())
        # clear all from Cache
        clear_cache()
        # Now the page should miss cache.
        self.get_miss(self.page_cachedpage.get_url())

    def test_clear_cache_url(self):
        u1 = self.page_cachedpage.get_url()
        u2 = self.page_cachedpage.get_url() + "?action=pytest"
        # First get should miss cache.
        self.get_miss(u1)
        self.get_miss(u2)
        # Second get should hit cache.
        self.get_hit(u1)
        self.get_hit(u2)
        # Clear only the second URL, using a regex.
        clear_cache(
            [
                r".*" + u1 + r"[\?\&]action=",
            ]
        )
        # url1 should still hit, but url2 should miss.
        self.get_hit(u1)
        self.get_miss(u2)

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
        self.assertEqual(
            response.get(self.header_name, None), Status.SKIP.value
        )
        response = self.client.post(reverse("cached_view"))
        self.assertEqual(
            response.get(self.header_name, None), Status.SKIP.value
        )
        # Register hook and assert it was actually registered.
        hooks.register("is_request_cacheable", hook_true)
        hook_fns = hooks.get_hooks("is_request_cacheable")
        self.assertEqual(hook_fns, [hook_true])
        # Setting `is_request_cachebale=True` does not really do much, because
        # the response still has the final say in whether or not the response is
        # cached. However a simple POST request where the response does not
        # forbid caching will in fact get cached!
        response = self.client.post(reverse("cached_view"))
        self.assertEqual(
            response.get(self.header_name, None), Status.MISS.value
        )
        response = self.client.post(reverse("cached_view"))
        self.assertEqual(response.get(self.header_name, None), Status.HIT.value)

    def test_request_hook_false(self):
        # Register hook and assert it was actually registered.
        hooks.register("is_request_cacheable", hook_false)
        hook_fns = hooks.get_hooks("is_request_cacheable")
        self.assertEqual(hook_fns, [hook_false])
        # The cached page should be force skipped due to the hook returning
        # false.
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
        # The no-cache page should be force cached due to the hook returning
        # true.
        self.get_miss(self.page_cachecontrolpage.get_url())
        self.get_hit(self.page_cachecontrolpage.get_url())

    def test_response_hook_false(self):
        # Register hook and assert it was actually registered.
        hooks.register("is_response_cacheable", hook_false)
        hook_fns = hooks.get_hooks("is_response_cacheable")
        self.assertEqual(hook_fns, [hook_false])
        # The cached page should be force skipped due to the hook returning
        # false.
        self.get_skip(self.page_cachedpage.get_url())
        self.get_skip(self.page_cachedpage.get_url())

    def test_response_hook_any(self):
        # Register hook and assert it was actually registered.
        hooks.register("is_response_cacheable", hook_any)
        hook_fns = hooks.get_hooks("is_response_cacheable")
        self.assertEqual(hook_fns, [hook_any])
        # The page should be cached normally due to hook returning garbage.
        self.test_page_hit()

    # ---- MODELS --------------------------------------------------------------
    def test_keyring_update_or_create(self):
        expiry = now() + datetime.timedelta(hours=1)
        key = "abc123"
        url = "https://example.com/"

        KeyringItem.objects.set(
            expiry=expiry,
            key=key,
            url=url,
        )
        self.assertEqual(KeyringItem.objects.count(), 1)
        self.assertEqual(KeyringItem.objects.first().url, url)

        expiry2 = now() + datetime.timedelta(hours=1)
        KeyringItem.objects.set(
            expiry=expiry2,
            key=key,
            url=url,
        )
        self.assertEqual(KeyringItem.objects.count(), 1)
        self.assertEqual(KeyringItem.objects.first().expiry, expiry2)

    def test_delete_expired(self):
        """
        Cache items expire by themselves, so we only need to actively
        delete database items
        """
        expiry1 = now() + datetime.timedelta(seconds=1)
        expiry2 = now() + datetime.timedelta(seconds=2)
        used_keys = []

        for exp in [expiry1, expiry2]:
            exp_iso = exp.isoformat()
            key = f"key-{exp_iso}"
            url = f"https://example.com/{exp_iso}"
            KeyringItem.objects.set(
                expiry=exp,
                key=key,
                url=url,
            )
            # Item should not expire
            self.cache.set(key, url, 100)
            used_keys.append(key)
        self.assertEqual(KeyringItem.objects.count(), 2)
        time.sleep(1)
        KeyringItem.objects.clear_expired()
        self.assertEqual(KeyringItem.objects.count(), 1)

        # Cache items remain
        for key in used_keys:
            self.assertTrue(self.cache.get(key))

    @override_settings(WAGTAIL_CACHE_BATCH_SIZE=2)
    def test_bulk_delete(self):
        """
        Bulk delete removes cache items and database items that refer to them
        """
        timeout = 10
        expiry = now() + datetime.timedelta(seconds=timeout)
        keys = [f"key-{counter}" for counter in range(8)]

        for key in keys:
            url = "https://example.com/"
            KeyringItem.objects.set(
                expiry=expiry,
                key=key,
                url=url,
            )
            self.cache.set(key, url, timeout)

        KeyringItem.objects.bulk_delete_cache_keys(keys[:4])

        for key in keys[:4]:
            self.assertFalse(KeyringItem.objects.filter(key=key).exists())
            self.assertFalse(self.cache.get(key))

        for key in keys[4:]:
            self.assertTrue(KeyringItem.objects.filter(key=key).exists())
            self.assertTrue(self.cache.get(key))

    @override_settings(WAGTAIL_CACHE_USE_RAW_DELETE=True)
    def test_bulk_delete_raw_delete(self):
        """
        You can optionally use Django's `_raw_delete`
        for speed with many cache keys.
        """
        timeout = 10
        expiry = now() + datetime.timedelta(seconds=timeout)
        keys = [f"key-{counter}" for counter in range(8)]

        for key in keys:
            url = "https://example.com/"
            KeyringItem.objects.set(
                expiry=expiry,
                key=key,
                url=url,
            )
            self.cache.set(key, url, timeout)

        KeyringItem.objects.bulk_delete_cache_keys(keys[:4])

        for key in keys[:4]:
            self.assertFalse(KeyringItem.objects.filter(key=key).exists())
            self.assertFalse(self.cache.get(key))

        for key in keys[4:]:
            self.assertTrue(KeyringItem.objects.filter(key=key).exists())
            self.assertTrue(self.cache.get(key))

    def test_active_for_url_regexes(self):
        past_expiry = now() - datetime.timedelta(seconds=1)
        future_expiry = now() + datetime.timedelta(seconds=1)
        url = "https://example.com"

        KeyringItem.objects.set(
            expiry=past_expiry,
            key="key",
            url=url,
        )
        KeyringItem.objects.set(
            expiry=future_expiry,
            key="key-2",
            url=url,
        )
        KeyringItem.objects.set(
            expiry=future_expiry,
            key="key-3",
            url=f"{url}/key-3/",
        )
        self.assertEqual(
            KeyringItem.objects.active_for_url_regexes(url).count(), 2
        )

    def test_active_for_urls_no_regexes(self):
        past_expiry = now() - datetime.timedelta(seconds=1)
        future_expiry = now() + datetime.timedelta(seconds=1)
        url = "https://example.com"
        url2 = "https://test.example.com"

        KeyringItem.objects.set(
            expiry=past_expiry,
            key="key",
            url=url,
        )
        KeyringItem.objects.set(
            expiry=future_expiry,
            key="key-2",
            url=url,
        )
        KeyringItem.objects.set(
            expiry=future_expiry,
            key="key-3",
            url=url2,
        )
        self.assertEqual(
            KeyringItem.objects.active_for_url_regexes().count(), 2
        )

    def test_keyringitem_str(self):
        future_expiry = datetime.datetime(year=2030, month=1, day=1)
        url = "https://example.com"

        KeyringItem.objects.set(
            expiry=future_expiry,
            key="key-2",
            url=url,
        )
        self.assertEqual(
            str(KeyringItem.objects.first()),
            "https://example.com -> key-2 (Expires: 2030-01-01 00:00:00+00:00)",
        )

    def test_batched(self):
        self.assertEqual(
            [batch for batch in batched("ABCDEFG", 3)],
            [("A", "B", "C"), ("D", "E", "F"), ("G",)],
        )

    def test_batched_invalid_batch_size(self):
        with self.assertRaises(ValueError):
            next(batched("ABCDEFG", 0))
