.. _badges:

.. image:: https://github.com/avanov/openapi-client-generator/workflows/CI/badge.svg?branch=develop
    :target: https://github.com/avanov/openapi-client-generator/actions?query=branch%3Adevelop

.. image:: https://coveralls.io/repos/github/avanov/openapi-client-generator/badge.svg?branch=develop
    :target: https://coveralls.io/github/avanov/openapi-client-generator?branch=develop

.. image:: https://requires.io/github/avanov/openapi-client-generator/requirements.svg?branch=master
    :target: https://requires.io/github/avanov/openapi-client-generator/requirements/?branch=master
    :alt: Requirements Status

.. image:: https://readthedocs.org/projects/openapi-client-generator/badge/?version=latest
    :target: https://openapi-client-generator.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: http://img.shields.io/pypi/v/openapi-client-generator.svg
    :target: https://pypi.python.org/pypi/openapi-client-generator
    :alt: Latest PyPI Release


OpenAPI Client Generator
========================

This CLI utility allows you to generate Python client packages from OpenAPI v3 specifications.
The project aims at supporting any generic valid specification.

Works on Python 3.8 and above.

You can install it from PyPI:

.. code-block:: bash

    pip install openapi-client-generator

Afterwards, use a CLI utility called ``openapi-client-generator``:

.. code-block:: bash

    $ openapi-client-generator --help
    usage: openapi-client-generator [-h] [-V] {gen} ...

    OpenAPI Client Generator

    optional arguments:
      -h, --help     show this help message and exit
      -V, --version  show program's version number and exit

    sub-commands:
      valid sub-commands

      {gen}          additional help
        gen          Generate client for a provided schema (JSON, YAML).


Cloning this repo
-----------------

The proper way to clone this repo is:

.. code-block:: bash

    git clone --recurse-submodules <repo-url> <local-project-root>
    cd <local-project-root>

    # for showing submodule status with `git status`
    git config status.submodulesummary 1

    # for logging submodule diff with `git diff`
    git config diff.submodule log

Documentation
-------------

Documentation is hosted on ReadTheDocs: https://openapi-client-generator.readthedocs.io/en/develop/


Test framework
--------------

The project uses `Nix <https://nixos.org/>`_ for bootstrapping its dev environment.

You can run existing test suite with

.. code::

   $ nix-shell --run "make test"


Changelog
---------

See `CHANGELOG <https://github.com/avanov/openapi-client-generator/blob/master/CHANGELOG.rst>`_.
