from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.cache.backends.locmem import LocMemCache


class ErroneousGetCache(LocMemCache):
    """
    Cache backend which throws an error when fetching from cache.
    """

    def get(self, key, default=None, version=None):
        raise Exception("Error in cache backend.")

    def has_key(self, key, version=None):
        raise Exception("Error in cache backend.")


class ErroneousSetCache(LocMemCache):
    """
    Cache backend which throws an error when setting/modifying cache.
    """

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        raise Exception("Error in cache backend.")

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        raise Exception("Error in cache backend.")

    def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        raise Exception("Error in cache backend.")

    def delete(self, key, version=None):
        raise Exception("Error in cache backend.")

    def clear(self):
        raise Exception("Error in cache backend.")
