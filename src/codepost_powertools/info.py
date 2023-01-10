"""
Info about the ``codepost-powertools`` package.

.. data:: package_name
   :type: str

   The default package name (tries to set from ``__package__`` with a
   fallback).

.. data:: version_info
   :type: ``Tuple[int, int, int]``

   The version info as a tuple of ints.

.. data:: __version__
   :type: |str|

   The version as a string.

.. data:: github_url
   :type: |str|

   A link to the GitHub repo.

.. data:: docs_url
   :type: |str|

   A link to the package documentation.

.. data:: docs_version_url
   :type: |str|

   A link to the package documentation for the current version.
"""

# =============================================================================

import sys

if sys.version_info >= (3, 8):
    from importlib import metadata as _metadata
else:
    import importlib_metadata as _metadata

# =============================================================================

__all__ = (
    "__version__",
    "version_info",
    "github_url",
    "docs_url",
    "docs_version_url",
)

# =============================================================================

package_name = __package__ or "codepost-powertools"

__version__ = _metadata.version(package_name)
# Assumes that `__version__` is only integers
version_info = tuple(map(int, __version__.split(".")))

github_url = "https://github.com/PrincetonCS-UCA/codepost-powertools"
_base_doc_url = "https://codepost-powertools.readthedocs.io/en/{version}/"
docs_url = _base_doc_url.format(version="latest")
docs_version_url = _base_doc_url.format(version=__version__)
