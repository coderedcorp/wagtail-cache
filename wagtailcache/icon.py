"""
Use a shiny fontawesome icon if available.
"""
from django.apps import apps


if apps.is_installed("wagtailfontawesome"):
    CACHE_ICON = "fa-bolt"
else:
    CACHE_ICON = "cog"
