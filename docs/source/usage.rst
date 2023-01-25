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

Google Sheets OAuth Credentials
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. |gspread package| replace:: ``gspread`` package
.. _gspread package: https://docs.gspread.org/en/latest/

This package interacts with Google Sheets through the |gspread package|_. You
can enable an OAuth Client to create, access, and edit spreadsheets using your
account.

To enable an OAuth Client, follow these steps:

1.  Go to the `Google Developers Console <https://console.cloud.google.com/>`_.
2.  Log in with the Google account you want to use with the OAuth Client. All
    created spreadsheets will be owned by this account in Google Drive, and all
    edits will be done with this account.
3.  In the top left, click the "Select a project" dropdown. Here, either select
    a project to use, or create a new one. The name and organization can be
    anything.

    .. note::
       If your account belongs to an organization, such as school accounts, this
       may not work depending on your workspace settings. If that happens, use a
       personal Google account with no organization.

4.  Go to the `API Library <https://console.cloud.google.com/apis/library>`_.
5.  In the search bar, search for "Google Drive API", select it, and enable it.
6.  Go back to the API Library. In the search bar, search for "Google Sheets
    API", select it, and enable it.
7.  Go to the
    `OAuth Consent Screen <https://console.cloud.google.com/apis/credentials/consent>`_
    tab.
8.  If prompted, select "External" for the User Type.
9.  On the "App Information" page, enter an app name. Select your email address
    for the support email. Scroll down to the bottom and enter your email
    address for the developer contact information. Click "Save and Continue".
10. On the "Scopes" page, click "Save and Continue".
11. On the "Test Users" page, add your email address as a user. Click "Save and
    Continue".
12. On the summary page, scroll to the bottom and click "Back to Dashboard".
13. Go to the `Credentials <https://console.cloud.google.com/apis/credentials>`_
    tab.
14. At the top of the page, select "+ Create credentials" > "OAuth client ID".
15. For the application type, select "Desktop app". Name your credentials. Click
    "Create".
16. At the popup, click "Download JSON".

    Alternatively, on the Credentials page, locate the credentials you just
    created in the "OAuth 2.0 Client IDs" table. Click the download button at
    the end of the row.
17. Rename the file to ``client_credentials.json`` and place it in your root
    folder.

.. note::
   The user interface of the Google Developers Console may be different when
   you're reading this. If it is, please submit an issue or pull request on the
   `GitHub repository <https://github.com/PrincetonCS-UCA/codepost-powertools/issues>`_.

.. note::
   The script will have access to all the Google Spreadsheets accessible by the
   account you use, including spreadsheets shared with you. While running the
   script, only spreadsheets that you specify will be accessed, so be sure to
   use the proper spreadsheets.

OAuth Client Authorization
^^^^^^^^^^^^^^^^^^^^^^^^^^

When using the package, if you've never authorized the app or if your
authorization has expired, you'll be given a URL in the console for you to visit
in order to authorize the app. Once that is done, a file named
``client_authorized.json`` will be created next to ``client_credentials.json``.
This will allow authentication to be cached for successive calls.

When you go to the URL, choose the account that you used to set up the OAuth
Client. It will then ask for access to your Google Account. Check the two
options "See, edit, create, and delete all of your Google Drive files" (from the
"Google Drive API") and "See, edit, create, and delete all of your Google Sheets
spreadsheets" (from the "Google Sheets API"). At the bottom, click "Continue".
You will be redirected to a page that says "The authentication flow has
completed. You may close this window." At this point, the script or command
should continue running.

.. warning::
   The credentials file and generated authorized client file contain sensitive
   data. Be sure to not share it with others. If you believe your information
   has been compromised, you will need to delete this OAuth Client and create a
   new one, as your Client ID and secret cannot be regenerated.

.. note::
   Visiting the authorization URL may show you a warning that the application
   has not been verified by Google. You may safely ignore this by clicking on
   "Advanced" and "Go to <project name> (unsafe)". If you are unsure about this,
   you can opt to use a service account instead. However, this is not yet
   supported.

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

Files will be appropriately named according to the command that generated it.
For some commands, a file may be generated for each student, in which case an
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
