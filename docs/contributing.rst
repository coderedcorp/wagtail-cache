Contributing
============

To set up your development environment, first create a new virtual environment
(in the ``.venv/`` folder):

(Linux or macOS)

.. code-block:: console

    $ python -m venv .venv
    $ source .venv/bin/activate

(Windows/PowerShell)

.. code-block:: ps1con

    PS> python -m venv .venv
    PS> .venv/Scripts/Activate.ps1


Enter the source code directory and install the package locally with additional
development tools:

.. code-block:: console

    $ pip install -r requirements-dev.txt


Write some code.

Next, run the static analysis tools (``flake8`` and ``mypy``)

.. code-block:: console

    $ flake8 ./wagtailcache/
    $ mypy ./wagtailcache/

Next, run the units tests. A simple Wagtail project using Wagtail Cache is in
the ``testproject/`` directory. The tests will generate a visual HTML file at
``htmlcov/index.html`` when finished, which you can open in your browser.

.. code-block:: console

    $ pytest ./testproject/

To build the documentation, run the following, which will output to the
``docs/_build/html/`` directory.

.. code-block:: console

    $ sphinx-build -M html ./docs/ ./docs/_build/ -W

To create a python package, run the following, which will output the package to
the ``dist/`` directory.

.. code-block:: console

    $ python setup.py sdist bdist_wheel
