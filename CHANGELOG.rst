Changelog
=========

`Unreleased`_
-------------

* Moved ``py.typed`` file to ``src/codepost_powertools`` so that it will be
  included in the distribution

* Changed ``get_path()`` to not expect the starting directory to exist

  * If the directory does exist, it is still required to be a directory.

* Removed unnecessary checks in ``get_assignment()``

  * codePost does not allow multiple assignments to have the same name, so there
    was no need to check for it.

* Better CLI help output with ``cloup``

* Added ``rubric`` group

  * Added ``export_rubric()`` function / ``export`` command

`v0.1.0`_ (2023-01-18)
----------------------

* Initial release

* Added ``grading`` group

  * Added ``create_ids_mapping()`` function / ``ids`` command

* Added CLI support

* Added docs

.. Links

.. _Unreleased: https://github.com/PrincetonCS-UCA/codepost-powertools/compare/v0.1.0...main
.. _v0.1.0: https://github.com/PrincetonCS-UCA/codepost-powertools/releases/tag/v0.1.0
