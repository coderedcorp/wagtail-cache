"""
Configuration file for the Sphinx documentation builder.

This file does only contain a selection of the most common options. For a
full list see the documentation:
http://www.sphinx-doc.org/en/master/config

-- Path setup --------------------------------------------------------------

If extensions (or modules to document with autodoc) are in another directory,
add these directories to sys.path here. If the directory is relative to the
documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys
sys.path.insert(0, os.path.abspath('.'))
"""

import datetime

from wagtailcache import __shortversion__


# -- Project information -----------------------------------------------------

project = "wagtail-cache"
author = "CodeRed LLC"
copyright = f"2018–{str(datetime.datetime.now().year)}, {author}"
# The short X.Y version
version = __shortversion__
# The full version, including alpha/beta/rc tags
release = __shortversion__
# -- General configuration ---------------------------------------------------
source_suffix = ".rst"

master_doc = "index"

language = "en"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

extensions = ["sphinx_wagtail_theme"]
# -- Options for HTML output -------------------------------------------------
html_show_sourcelink = False

html_theme = "sphinx_wagtail_theme"

html_sidebars = {"**": ["searchbox.html", "globaltoc.html", "sponsor.html"]}

html_theme_options = {
    "project_name": "wagtail-cache",
    "github_url": "https://github.com/coderedcorp/wagtail-cache/blob/main/docs/",
    "footer_links": (
        "Wagtail Hosting by CodeRed|https://www.codered.cloud/,"
        "Wagtail Cache on GitHub|https://github.com/coderedcorp/wagtail-cache,"
        "About CodeRed|https://www.coderedcorp.com/"
    ),
}

html_last_updated_fmt = ""
