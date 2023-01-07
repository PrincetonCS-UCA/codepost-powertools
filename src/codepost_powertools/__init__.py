"""
__init__.py
The `codepost_powertools` package.
"""

# =============================================================================

from codepost_powertools import grading

# Implicitly run the config file
from codepost_powertools.config import log_in_codepost
from codepost_powertools.version import __version__

# =============================================================================

__all__ = (
    "log_in_codepost",
    "grading",
)
