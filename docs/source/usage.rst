Usage
=====

Installation
------------

.. code-block:: bash

   $ pip install codepost-powertools

Requires Python 3.7.2+.

.. _Root folder:

Root Folder
-----------

You should use a dedicated folder for the usage of these tools, since it
requires an input config file and outputs files for certain commands and
functions. For instance:

.. code-block:: bash

   $ GRADING_FOLDER=codePostGrading
   $ mkdir $GRADING_FOLDER
   $ cd $GRADING_FOLDER
   # You can now create the config file in this folder
   GRADING_FOLDER $ echo "api_key: $CP_API_KEY" > config.yaml

It is also recommended to use a virtual environment:

.. code-block:: bash

   GRADING_FOLDER $ VENV=env
   GRADING_FOLDER $ python -m venv $VENV
   GRADING_FOLDER $ source $VENV/bin/activate
   (VENV) GRADING_FOLDER $ python -m pip install codepost-powertools
   # You can now use the package
   (VENV) GRADING_FOLDER $ cptools --help
   (VENV) GRADING_FOLDER $ python my_script.py

In the rest of the documentation, it is assumed that your current directory is
this folder and that you have access to the package, either through a global
installation or through a virtual environment.

Configuration File
------------------

By default, the package will look for a configuration file called
``config.yaml`` that contains a field ``"api_key"`` for your codePost API key.
See `here <https://docs.codepost.io/docs#2-obtaining-your-codepost-api-key>`_
for instructions on how to access your codePost API key, as well as more
information on the config YAML file. You must have admin access to all the
courses you wish to access with this package.

Here is what the ``config.yaml`` file may look like:

.. code-block:: yaml

   api_key: YOUR_API_KEY_HERE

.. note::
   This package *does not* use the default ``codepost-config.yaml`` file that
   the ``codepost`` package uses. However, you can pass a custom path to your
   config file to :meth:`~codepost_powertools.log_in_codepost` if you wish.

Output Files
------------

The following applies to both commands and functions, and they are used
interchangeably.

For certain commands, an output file will be created. To keep these outputs
organized, they will be saved according to the following:

1. All output files will be saved in the folder ``output/``.
2. If the output file pertains to an entire course, it will be saved in the
   folder ``output/<COURSE>/``, where ``<COURSE>`` is a combination of the
   course name and period.
3. If the output file pertains to an assignment, it will be saved in the folder
   ``output/<COURSE>/<ASSIGNMENT>``, where ``<ASSIGNMENT>`` is the assignment
   name.

Files will be appropriate named according to the command that generated it. For
some commands, a file may be generated for each student, in which case an
appropriately named folder will be created, either under ``output/<COURSE>/``
or ``output/<COURSE>/<ASSIGNMENT>/``, with each file named for each student.

In the documentation of commands and functions, whenever ``<OUTPUT>/file.csv``
appears, it means that a file named ``file.csv`` will be saved at the
appropriate output path, according to the above.

Command Line Interface
----------------------

You can access the command-line interface with the ``cptools`` command:

.. code-block:: bash

   $ cptools --help

   Usage: cptools [OPTIONS] COMMAND [ARGS]...

     The `codepost_powertools` package on the command line.

Please see :doc:`cli` for more information.

Importing in Scripts
--------------------

You can import the package in a script:

.. code-block:: python

   import codepost_powertools as cptools
   
   # Log in to codePost
   cptools.log_in_codepost()

   # Call methods

Please see :doc:`scripting` for more information.
