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

Development
-----------

For commands that require the virtual environment, prefix the command with
``poetry run``:

.. code-block:: bash

   ROOT/codepost-powertools $ poetry run pytest
   ROOT/codepost-powertools $ poetry run mypy src

Alternatively, start the Poetry shell:

.. code-block:: bash

   ROOT/codepost-powertools $ poetry shell
   (codepost-powertools-py3.X) ROOT/codepost-powertools $ pytest
   (codepost-powertools-py3.X) ROOT/codepost-powertools $ mypy src

To run the Powertools CLI, you must be in the root folder. Since the ``poetry``
command requires a visible ``pyproject.toml`` file, you will need to activate
the virtual environment before switching back to the root folder.

.. code-block:: bash

   ROOT/codepost-powertools $ poetry shell
   (codepost-powertools-py3.X) ROOT/codepost-powertools $ cd ..
   (codepost-powertools-py3.X) ROOT $ cptools ...

It might be easier to have a separate terminal tab/window open for this purpose.

Testing
-------

.. |pytest| replace:: ``pytest``
.. _pytest: https://docs.pytest.org/

.. |mypy| replace:: ``mypy``
.. _mypy: https://mypy.readthedocs.io/

The tests are defined in the ``tests/`` directory using |pytest|_. The
``pyproject.toml`` file is already configured to run the tests with the command:

.. code-block:: bash

   ROOT/codepost-powertools $ poetry run pytest
   # Or, with the virtual environment activated:
   (codepost-powertools-py3.X) ROOT/codepost-powertools $ pytest

The codebase is also statically type-checked using |mypy|_:

.. code-block:: bash

   ROOT/codepost-powertools $ poetry run mypy src
   # Or, with the virtual environment activated:
   (codepost-powertools-py3.X) ROOT/codepost-powertools $ mypy src

Note that there are a few expected warnings that are explained at
:doc:`contributing/mypy-warnings`.
