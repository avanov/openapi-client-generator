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
