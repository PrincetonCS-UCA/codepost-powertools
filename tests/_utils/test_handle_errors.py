"""
Tests the error handler.
"""

# =============================================================================

import pytest

from codepost_powertools._utils import handle_errors
from tests.helpers import parametrize

# =============================================================================


@parametrize(
    {
        "exception": ValueError,
        "message": "Invalid {}: {value}",
        "args": ["value"],
        "kwargs": {"value": "some bad value"},
    },
    {
        "exception": IndexError,
        "message": "Index {index} not good: {} does not have {} {index} items",
        "args": ["empty list", "more than"],
        "kwargs": {"index": "0"},
    },
)
def test_handle_error(track_logs, exception, message, args, kwargs):
    expected_msg = message.format(*args, **kwargs)
    # check exception (log = False)
    with pytest.raises(exception) as exc_info:
        handle_errors.handle_error(False, exception, message, *args, **kwargs)
    assert str(exc_info.value) == expected_msg
    # check log (log = True)
    track_logs.reset("ERROR")
    handle_errors.handle_error(True, exception, message, *args, **kwargs)
    assert track_logs.saw_msg_logged("ERROR", expected_msg, exact=True)
