Contributing
============

Dependencies
------------

This project uses `Poetry <https://python-poetry.org/>`_ to manage dependencies,
virtual environments, builds, and packaging. Install it by following the
instructions `here <https://python-poetry.org/docs/#installation>`_.

Environment
-----------

Setup:

1. Clone the repo:
  
   .. code-block:: bash

      $ git clone https://github.com/PrincetonCS-UCA/codepost-powertools.git
      $ cd codepost-powertools

2. Create/update the virtual environment with Poetry:

   .. code-block:: bash

      $ poetry install
  
   If editing the docs, be sure to include the optional ``docs`` group:

   .. code-block:: bash

      $ poetry install --with docs

To run the Powertools CLI, use the following command:

.. code-block:: bash

   $ poetry run cptools ...

Remember to prefix ``poetry run`` for any commands that require the virtual
environment.

Alternatively, start the Poetry shell:

.. code-block:: bash

   $ poetry shell
   (codepost-powertools-py3.X) $ cptools ...
