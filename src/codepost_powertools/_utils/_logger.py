"""
_logger.py
Gets a logger to log messages or do nothing.
"""

# =============================================================================

import sys

from loguru import logger

# =============================================================================

# Configure global logger
# - Do not diagnose exceptions
# - Set min level to 0 to show all logs
logger.remove()
logger.add(sys.stderr, diagnose=False, level=0)

# =============================================================================


class NullLogger:
    """A 'logger' that doesn't do anything.

    This object acts as a linked list to itself: it returns itself on
    all attribute accesses and when called.
    """

    def __call__(self, *args, **kwargs):
        return self

    def __getattribute__(self, key):
        return self


_null_logger = NullLogger()

# =============================================================================


def _get_logger(log: bool):
    """Gets a logger to log messages or do nothing based on `log`.

    Args:
        log (bool): Whether to show log messages.
    """
    return logger if log else _null_logger
