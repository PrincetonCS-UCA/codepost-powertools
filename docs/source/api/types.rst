.. include:: ../_shared.rst

Type Aliases
============

codePost Types
--------------

.. _codePost API Reference: https://docs.codepost.io/reference/welcome-api-v10
.. _codePost Python SDK: https://github.com/codepost-io/codepost-python

Please see the `codePost API Reference`_ and the `codePost Python SDK`_.

These types are imported into a single module in ``codepost_powertools`` in
:file:`codepost_powertools.utils.cptypes`.

.. code-block:: python

   from codepost_powertools.utils.codepost_utils import get_course
   from codepost_powertools.utils.cptypes import Course

   course: Optional[Course] = get_course("COS126", "F2022")

Powertools Aliases
------------------

.. automodule:: codepost_powertools.utils.types
