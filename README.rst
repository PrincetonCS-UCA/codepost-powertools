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

The documentation can be found
`here <https://codepost-powertools.readthedocs.io/en/latest/)>`_.

.. start-overview

Installation
------------

.. code-block:: bash

   $ pip install codepost-powertools

Usage
-----

You should have a dedicated folder for the usage of these tools, since it
requires an input config file and outputs files for certain commands /
functions. It is recommended to use a virtual environment for this:

.. code-block:: bash

   $ python -m venv env
   $ source env/bin/activate
   (env) $ python -m pip install codepost-powertools
   (env) $ cptools --help
   (env) $ python my_script.py

By default, the package will look for a configuration file called
``config.yaml`` that contains a field ``"api_key"`` for your codePost API key.
See `here <https://docs.codepost.io/docs#2-obtaining-your-codepost-api-key>`_
for instructions on how to access your codePost API key, as well as more
information on the config YAML file.

.. note::
   This package *does not* use the default ``codepost-config.yaml`` file that
   the ``codepost`` package uses. However, you can pass a custom path to your
   config file to :meth:`~codepost_powertools.log_in_codepost` if you wish.

Command Line Usage
^^^^^^^^^^^^^^^^^^

You can access the command-line interface with the ``cptools`` command:

.. code-block:: bash

   $ cptools --help

   Usage: cptools [OPTIONS] COMMAND [ARGS]...

     The `codepost_powertools` package on the command line.

Please see |CLI docs| for more information.

Script Usage
^^^^^^^^^^^^

You can import the package in a script:

.. code-block:: python

   import codepost_powertools as cptools
   
   # Log in to codePost
   cptools.log_in_codepost()

   # Call methods

Please see |Scripting docs| for more information.

.. end-overview

.. When the README is viewed on its own, can't provide a link
.. |CLI docs| replace:: the CLI documentation
.. |Scripting docs| replace:: the "Writing Scripts" documentation
