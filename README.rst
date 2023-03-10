codePost Powertools
===================

.. badges

.. image:: https://readthedocs.org/projects/codepost-powertools/badge/?version=latest
   :target: https://codepost-powertools.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. |codePost SDK| replace:: ``codePost`` SDK
.. _codePost SDK: https://github.com/codepost-io/codepost-python

Some helpful codePost tools to aid with grading flow using the |codePost SDK|_!

These tools were originally created to support the grading process for COS126,
the introductory Computer Science course at Princeton University.

.. end-intro

Documentation
-------------

Please see
`the documentation <https://codepost-powertools.readthedocs.io/en/latest/>`_
for more detailed descriptions of the package.

.. The "Usage" page in the documentation is a more detailed version of the
   below. Note that it does not include it directly, since this file must be
   PyPi-compliant. See:
   https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/#validating-restructuredtext-markup

Installation
------------

.. code-block:: bash

   $ pip install codepost-powertools

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

Command Line Interface
----------------------

You can access the command-line interface with the ``cptools`` command:

.. code-block:: bash

   $ cptools --help

   Usage: cptools [OPTIONS] COMMAND [ARGS]...

     The `codepost_powertools` package on the command line.

Please see the CLI documentation page for more information.

Importing in Scripts
--------------------

You can import the package in a script:

.. code-block:: python

   import codepost_powertools as cptools
   
   # Log in to codePost
   cptools.log_in_codepost()

   # Call methods

Please see the "Writing Scripts" documentation page for more information.
