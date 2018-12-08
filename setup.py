#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

setup(
    name='wagtail-cache',
    version='0.1.0',
    author="CodeRed LLC",
    author_email='info@coderedcorp.com',
    url='https://github.com/coderedcorp/wagtail-cache',
    description="A simple page cache for Wagtail",
    long_description=readme,
    license="BSD license",
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        'wagtail>=2.0',
        'django>=2.0',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        'Framework :: Wagtail',
        'Framework :: Wagtail :: 2',
    ],
)
