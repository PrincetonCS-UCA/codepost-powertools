:orphan:

``mypy`` warnings
=================

This page explains some ``mypy`` warnings in the code that can be ignored.

Last updated: 2023-01-23, v0.2.0.

* ``arg-type`` errors in:

  * ``src/codepost_powertools/_utils/file_io.py``
  * ``src/codepost_powertools/grading/ids.py``

  .. code-block:: text

     [file_io.py:137] Argument 3 to "handle_error" has incompatible type "Optional[str]"; expected "str"
     [ids.py:151] Argument 2 to "save_csv" has incompatible type "Optional[Path]"; expected "Union[PathLike[Any], str]"

  These errors involve the ``SuccessOrNone[T]`` and ``SuccessOrErrorMsg`` types.
  They are defined as a tuple with a "success" flag and something else, but the
  types when ``success = True`` and when ``success = False`` are different, but
  still exactly and distinctly defined. Thus, if there is an ``if`` statement
  checking the value of ``success``, the other value's type is definitely known
  within the body. However, ``mypy`` does not recognize this, and gives errors.

  Additional conditionals can be put into the ``if`` statements to also check if
  the other value is ``None``, but that would be redundant and only for the
  purpose of satisfying the type-checker. We have decided that that is not a
  good enough reason to change the code, and instead this error will remain.
  However, this means that more instances of this error will likely come up as
  more code is written.
