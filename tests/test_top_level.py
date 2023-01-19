"""
Tests the top level functions.
"""

# =============================================================================

import codepost.util.config
import pytest

import codepost_powertools as cptools
from tests.helpers import parametrize, parametrize_indirect

# =============================================================================

# `log_in_codepost()` patterns
CONFIG_FILE_NOT_FOUND_ERROR = r"Config file not found"
CONFIG_FILE_NOT_READ_ERROR = r"Config file could not be read"
CONFIG_FILE_NO_KEY_ERROR = r'Config file does not contain ".+" key'
CONFIG_FILE_INVALID_KEY_ERROR = r"Config file has invalid codePost API key"

# =============================================================================


class TestLogInCodepost:
    """Tests the function :func:`~codepost_powertools.log_in_codepost`."""

    @parametrize(
        {
            "tmp_file": "config.yaml",
            "exception": FileNotFoundError,
            "error_pattern": CONFIG_FILE_NOT_FOUND_ERROR,
        },
        {
            "tmp_file": ("config.txt", ""),
            "exception": RuntimeError,
            "error_pattern": CONFIG_FILE_NOT_READ_ERROR,
        },
        {
            # YAML files must have a top-level mapping to be valid
            "tmp_file": ("config.yaml", ""),
            "exception": RuntimeError,
            "error_pattern": CONFIG_FILE_NOT_READ_ERROR,
        },
        {
            "tmp_file": ("config.yaml", "key: value"),
            "exception": KeyError,
            "error_pattern": CONFIG_FILE_NO_KEY_ERROR,
        },
        {
            "tmp_file": ("config.yaml", "api_key: value"),
            "exception": ValueError,
            "error_pattern": CONFIG_FILE_INVALID_KEY_ERROR,
        },
        {
            "tmp_file": ("config.yaml", "api_key: null"),
            "exception": ValueError,
            "error_pattern": CONFIG_FILE_INVALID_KEY_ERROR,
        },
        {
            "tmp_file": ("config.yaml", "api_key: ['an', 'array']"),
            "exception": ValueError,
            "error_pattern": CONFIG_FILE_INVALID_KEY_ERROR,
        },
        indirect=["tmp_file"],
    )
    def test_error(self, track_logs, tmp_file, exception, error_pattern):
        # check exception
        with pytest.raises(exception, match=error_pattern):
            cptools.log_in_codepost(config_file=tmp_file, log=False)
        # check error logs
        track_logs.reset("ERROR")
        success = cptools.log_in_codepost(config_file=tmp_file, log=True)
        assert not success
        assert track_logs.saw_level_logged("ERROR")
        assert track_logs.saw_msg_logged("ERROR", error_pattern)

    @parametrize_indirect(
        {"tmp_file": ("config.yaml", "api_key: test_value")},
        {"tmp_file": ("config.yaml", "api_key: some random value")},
    )
    def test_no_error(self, track_no_error_logs, tmp_file):
        with pytest.MonkeyPatch.context() as monkeypatch:
            # return true for validating codepost api keys
            monkeypatch.setattr(
                codepost.util.config,
                "validate_api_key",
                lambda *args, **kwargs: True,
            )
            success = cptools.log_in_codepost(config_file=tmp_file, log=True)
            assert success
