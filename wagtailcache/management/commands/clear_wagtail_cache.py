"""CLI tool to clear wagtailcache."""
from django.core.management.base import BaseCommand

from wagtailcache.cache import clear_cache


class Command(BaseCommand):
    help = "Clears the cache for the entire site."

    def handle(self, *args, **options):
        clear_cache()
