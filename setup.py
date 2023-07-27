from setuptools import find_packages
from setuptools import setup

from wagtailcache import __version__


with open("README.md", encoding="utf8") as readme_file:
    readme = readme_file.read()

setup(
    name="wagtail-cache",
    version=__version__,
    author="CodeRed LLC",
    author_email="info@coderedcorp.com",
    url="https://github.com/coderedcorp/wagtail-cache",
    description="A simple page cache for Wagtail based on the Django cache middleware.",
    long_description=readme,
    long_description_content_type="text/markdown",
    license="BSD license",
    include_package_data=True,
    packages=find_packages(),
    install_requires=["wagtail>=3.0,<6"],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Framework :: Django",
        "Framework :: Wagtail",
        "Framework :: Wagtail :: 3",
        "Framework :: Wagtail :: 4",
        "Framework :: Wagtail :: 5",
    ],
)
