from typing import List

from django.core.cache import caches
from django.db import models
from django.db.models import Q
from django.utils.timezone import now

from wagtailcache.settings import wagtailcache_settings
from wagtailcache.utils import batched


class KeyringItemManager(models.Manager):
    def __init__(self):
        super().__init__()
        self._wagcache = caches[wagtailcache_settings.WAGTAIL_CACHE_BACKEND]

    def set(self, url, key, expiry) -> models.Model:
        """
        Create or update a keyring item, clearing expired items too.
        """
        item, _ = self.update_or_create(
            defaults={"expiry": expiry},
            url=url,
            key=key,
        )
        self.clear_expired()
        return item

    def bulk_delete_cache_keys(self, keys: List[str]) -> None:
        """
        Bulk delete the keys that exist, in batches
        """
        existing_keys = self.filter(key__in=keys)
        # Delete from cache
        for key_batch in batched(
            existing_keys.values_list("key", flat=True),
            wagtailcache_settings.WAGTAIL_CACHE_BATCH_SIZE,
        ):
            self._wagcache.delete_many(key_batch)
        # Delete from database
        existing_keys.delete()

    def clear_expired(self) -> None:
        """
        Clear all items whose expiry has passed.
        """
        self.filter(expiry__lt=now()).delete()

    def active(self):
        return self.filter(expiry__gt=now())

    def active_for_url_regexes(self, urls):
        if urls is None:
            urls = []
        if not isinstance(urls, (list, tuple)):
            urls = list(urls)
        qs = self.active()
        if not urls:
            return qs
        q_objects = Q()
        for url in urls:
            q_objects.add(Q(url__regex=url), Q.OR)
        return qs.filter(q_objects)


class KeyringItem(models.Model):
    """
    KeyringItems relate the URL of a page on the site to the key of an item
    in the cache.
    """

    expiry = models.DateTimeField()
    key = models.CharField(max_length=512)
    url = models.URLField()

    objects = KeyringItemManager()

    class Meta:
        ordering = ["url"]
        indexes = [
            models.Index(fields=["expiry"]),
            models.Index(fields=["key"]),
            models.Index(fields=["url"]),
        ]
        unique_together = [["url", "key"]]

    def __str__(self):
        return f"{self.url} -> {self.key} (Expires: {self.expiry})"
