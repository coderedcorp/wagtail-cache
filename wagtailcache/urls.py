"""
URLs for the wagtail admin dashboard.
"""

from django.urls import path
from wagtailcache.views import index, clear


urlpatterns = [
    path('', index, name="index"),
    path('clearcache', clear, name="clearcache"),
]
