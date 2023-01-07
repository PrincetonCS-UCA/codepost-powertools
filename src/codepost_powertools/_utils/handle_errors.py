"""
handle_errors.py
Handles errors.
"""

# =============================================================================

from typing import Type

from codepost_powertools._utils._logger import _get_logger

# =============================================================================

# If logging an error, always display it
# Set depth to 1 so that the caller location is shown in the log
_error_logger = _get_logger(log=True).opt(depth=1)

# =============================================================================


def handle_error(
    log: bool, exception: Type[BaseException], msg: str, *args, **kwargs
):
    """Handles an error by logging the message or raising an exception.

    Args:
        log (bool): Whether to show log messages.
            If False, the given exception will be raised instead.
        exception (Type[BaseException]): The exception type to raise.
            The formatted message will be passed as the first argument.
        msg (str): The message.
        *args, **kwargs: Additional arguments to be given to
            `msg.format()`.
    """
    if log:
        _error_logger.error(msg, *args, **kwargs)
        return
    raise exception(msg.format(*args, **kwargs))
