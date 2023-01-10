"""
The ``codepost_powertools`` package.
"""

# =============================================================================

from codepost_powertools.info import __version__  # isort: skip

# =============================================================================

from codepost_powertools import grading

# Implicitly run the config file
from codepost_powertools.config import log_in_codepost

# =============================================================================

__all__ = (
    "log_in_codepost",
    "grading",
)
