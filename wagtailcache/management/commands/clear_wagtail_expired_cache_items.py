from django.core.management.base import BaseCommand
from wagtailcache.models import KeyringItem

class Command(BaseCommand):
    help = 'Clear expired KeyringItems from the database'

    def handle(self, *args, **options):
        try:
            cleared_count = KeyringItem.objects.clear_expired()
            msg = f"Successfully cleared {cleared_count} expired KeyringItems"
            self.stdout.write(self.style.SUCCESS(msg))
        except Exception as e:
            msg = f"Failed to clear expired KeyringItems: {e}"
            self.stdout.write(self.style.ERROR(msg))
