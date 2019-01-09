from django_redis.cache import omit_exception, RedisCache as BaseBackend


class RedisCache(BaseBackend):
    """
    Extends django_redis.cache.RedisCache for compatiblity
    with the Django cache middleware.
    """
    @omit_exception
    def set(self, *args, **kwargs):
        """
        Return the value instead of a boolean.
        """
        super().set(*args, **kwargs)
        return args[1]
