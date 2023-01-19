Contributing
============

Dependencies
------------

This project requires Python 3.7.2+.

This project uses `Poetry <https://python-poetry.org/>`_ to manage dependencies,
virtual environments, builds, and packaging. Install it by following the
instructions `here <https://python-poetry.org/docs/#installation>`_.

Environment
-----------

1. Create a root folder for the package, as outlined at :ref:`Root folder`:

   .. code-block:: bash

      $ ROOT=powertools-dev
      $ mkdir $ROOT
      $ cd $ROOT

2. Clone the repo:

   .. code-block:: bash

      ROOT $ git clone https://github.com/PrincetonCS-UCA/codepost-powertools.git
      ROOT $ cd codepost-powertools

3. Create/update the virtual environment with Poetry:

   .. code-block:: bash

      ROOT/codepost-powertools $ poetry install --with dev

   If editing the docs, be sure to include the optional ``docs`` group:

   .. code-block:: bash

      ROOT/codepost-powertools $ poetry install --with dev,docs

Writing Code
------------

.. |pylint| replace:: ``pylint``
.. _pylint: https://pylint.pycqa.org/

.. |black| replace:: ``black``
.. _black: https://black.readthedocs.io/

.. |isort| replace:: ``isort``
.. _isort: https://pycqa.github.io/isort/

* The code is linted with |pylint|_. See the ``.pylintrc`` file for the
  configuration.
* The code is formatted with |black|_, using a line length of 79 characters.
* Imports are formatted with |isort|_, using the ``black`` profile. See the
  ``pyproject.toml`` file for the configuration.

Running Commands
----------------

*  For commands that require the virtual environment, prefix the command with
   ``poetry run``:

   .. code-block:: bash

      ROOT/codepost-powertools $ poetry run pytest
      ROOT/codepost-powertools $ poetry run mypy src

   Alternatively, start the Poetry shell:

   .. code-block:: bash

      ROOT/codepost-powertools $ poetry shell
      (codepost-powertools-py3.X) ROOT/codepost-powertools $ pytest
      (codepost-powertools-py3.X) ROOT/codepost-powertools $ mypy src

*  To run the Powertools CLI, you must be in the root folder. Since the
   ``poetry`` command requires a visible ``pyproject.toml`` file, you will need
   to activate the virtual environment before switching back to the root folder.

   .. code-block:: bash

      ROOT/codepost-powertools $ poetry shell
      (codepost-powertools-py3.X) ROOT/codepost-powertools $ cd ..
      (codepost-powertools-py3.X) ROOT $ cptools ...

   It might be easier to have a separate terminal tab/window open for this
   purpose.

Testing
-------

.. |pytest| replace:: ``pytest``
.. _pytest: https://docs.pytest.org/

.. |mypy| replace:: ``mypy``
.. _mypy: https://mypy.readthedocs.io/

.. |coverage| replace:: ``coverage``
.. _coverage: https://coverage.readthedocs.io/

*  The tests are defined in the ``tests/`` directory using |pytest|_. The
   ``pyproject.toml`` file is already configured to run the tests with the
   command:

   .. code-block:: bash

      ROOT/codepost-powertools $ poetry run pytest
      # Or, with the virtual environment activated:
      (codepost-powertools-py3.X) ROOT/codepost-powertools $ pytest

*  The codebase can be statically type-checked using |mypy|_:

   .. code-block:: bash

      ROOT/codepost-powertools $ poetry run mypy src
      # Or, with the virtual environment activated:
      (codepost-powertools-py3.X) ROOT/codepost-powertools $ mypy src

   Note that there are a few expected warnings that are explained at
   :doc:`contributing/mypy-warnings`.

*  Test the test coverage with |coverage|_:

   .. code-block:: bash

      ROOT/codepost-powertools $ poetry run coverage run -m pytest
      # Or, with the virtual environment activated:
      (codepost-powertools-py3.X) ROOT/codepost-powertools $ coverage run -m pytest

   Note that there are no tests written for the CLI, so files pertaining to that
   will not have full coverage.

Documentation
-------------

.. |Sphinx| replace:: Sphinx
.. _Sphinx: https://www.sphinx-doc.org/en/master/

.. |Read the Docs| replace:: Read the Docs
.. _Read the Docs: https://docs.readthedocs.io/

The documentation is written in the ``docs/`` folder using |Sphinx|_ and hosted
on |Read the Docs|_.

To build the documentation, run the following:

.. code-block:: bash

   (codepost-powertools-py3.X) ROOT/codepost-powertools $ cd docs
   (codepost-powertools-py3.X) ROOT/codepost-powertools/docs $ make html

To activate a local server at http://localhost:8000/ that auto-updates on
changes, run the following:

.. code-block:: bash

   (codepost-powertools-py3.X) ROOT/codepost-powertools/docs $ make livehtml
