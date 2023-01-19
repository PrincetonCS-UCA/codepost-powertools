"""
Private utilities.

.. warning::
   Utilities in this subpackage do not need to maintain backward
   compatibility with previous versions, as they are private utilities
   meant to be used as internal helpers. Therefore, behavior of these
   functions may change, even between minor or patch versions.
"""

# =============================================================================

from codepost_powertools._utils._logger import _get_logger
from codepost_powertools._utils.handle_errors import handle_error

# =============================================================================

__all__ = ("handle_error",)
