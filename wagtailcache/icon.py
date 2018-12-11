"""
Use a shiny fontawesome icon if available.
"""

try:
    import wagtailfontawesome
    CACHE_ICON = 'fa-bolt'
except ModuleNotFoundError:
    CACHE_ICON = 'cog'
