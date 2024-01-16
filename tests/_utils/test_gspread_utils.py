"""
Tests the ``gspread`` utilities.
"""

# =============================================================================

import gspread
import pytest

from codepost_powertools._utils import gspread_utils
from tests.helpers import (
    MockFunction,
    get_request_param,
    parametrize,
    parametrize_indirect,
)
from tests.mocks import MockClient

# =============================================================================

# `authenticate_client()` patterns
MISSING_CREDENTIALS_FILE_ERROR = r"OAuth credentials file not found"
INVALID_CREDENTIALS_FILE_ERROR = r"OAuth credentials file is not a file"
CREDENTIALS_EXPIRED_WARNING = r"OAuth Client credentials expired; refreshing"

# `open_spreadsheet()` patterns
SPREADSHEET_NOT_FOUND_ERROR = r"Spreadsheet .+ not found"

# =============================================================================


class TestAuthenticateClient:
    """Tests the function
    :func:`~codepost_powertools._utils.gspread_utils.authenticate_client`.
    """

    class MockGspreadOauth(MockFunction):
        """A mock for the :func:`gspread.oauth` function."""

        def __init__(self, kwargs):
            super().__init__(enable_set=True)
            self._kwargs = kwargs
            self._auth_file_existed = []

        def auth_file_existed(self, call_index):
            """Returns whether the authorized user file existed before
            the specified call.
            """
            if not 0 <= call_index < self._times_called:
                raise IndexError("invalid call index")
            return self._auth_file_existed[call_index]

        def mock(
            self,
            scopes=None,
            flow=None,
            credentials_filename=None,
            authorized_user_filename=None,
            client_factory=None,
        ):
            if authorized_user_filename is None:
                # testing will create the file, so we will require that
                # it's passed in
                raise ValueError("must provide authorized user filename")
            client = MockClient(**self._kwargs)
            # check if the file already existed
            self._auth_file_existed.append(authorized_user_filename.exists())
            # always create the authorized user file
            authorized_user_filename.touch()
            return client

    @pytest.fixture(name="gspread_patch_oauth", autouse=True)
    def fixture_gspread_patch_oauth(self, request):
        """Patches the ``gspread.oauth()`` function.

        Accepts the following kwargs:
            expired (bool): Whether the returned client is expired.
            spreadsheet_success (bool): Whether opening a spreadsheet is
                successful.
        """
        kwargs = get_request_param(request, default={})
        mock_func = self.MockGspreadOauth(kwargs)
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setattr(gspread, "oauth", mock_func)
            yield mock_func

    @parametrize_indirect(
        {"tmp_file": "credentials.json"},
        {"tmp_file": "client.json"},
    )
    def test_missing_credentials_file(self, track_logs, tmp_file):
        # check exception
        with pytest.raises(
            FileNotFoundError, match=MISSING_CREDENTIALS_FILE_ERROR
        ):
            gspread_utils.authenticate_client(
                credentials_file=tmp_file, log=False
            )
        # check logs
        track_logs.reset("ERROR")
        success, client = gspread_utils.authenticate_client(
            credentials_file=tmp_file, log=True
        )
        assert not success
        assert client is None
        assert track_logs.saw_msg_logged(
            "ERROR", MISSING_CREDENTIALS_FILE_ERROR
        )

    @parametrize_indirect(
        {"tmp_file": (["credentials.json", "client.json"], "")},
        {"tmp_file": (["credentials", "credentials.json"], "")},
        {"tmp_file": (["client.json", "credentials.json"], "credentials")},
    )
    def test_non_file_credentials(self, track_logs, tmp_file):
        # the parent is a directory, not a file
        credentials_file = tmp_file.parent
        # check exception
        with pytest.raises(OSError, match=INVALID_CREDENTIALS_FILE_ERROR):
            gspread_utils.authenticate_client(
                credentials_file=credentials_file, log=False
            )
        # check logs
        track_logs.reset("ERROR")
        success, client = gspread_utils.authenticate_client(
            credentials_file=credentials_file, log=True
        )
        assert not success
        assert client is None
        assert track_logs.saw_msg_logged(
            "ERROR", INVALID_CREDENTIALS_FILE_ERROR
        )

    @parametrize_indirect(
        {
            "tmp_file": ("credentials.json", "credentials"),
            "gspread_patch_oauth": {"expired": True},
        }
    )
    def test_expired_client(
        self, track_no_error_logs, track_logs, gspread_patch_oauth, tmp_file
    ):
        track_logs.reset("WARNING")
        success, client = gspread_utils.authenticate_client(
            credentials_file=tmp_file, log=True
        )
        assert success
        assert client is not None
        assert gspread_patch_oauth.times_called > 1
        assert track_logs.saw_msg_logged(
            "WARNING", CREDENTIALS_EXPIRED_WARNING, exact=True
        )

    @parametrize_indirect(
        {"tmp_file": ("credentials.json", "credentials")},
    )
    def test_force_reauth(
        self, track_no_error_logs, gspread_patch_oauth, tmp_file
    ):
        # mock that the authorized user file exists
        auth_user_file = tmp_file.with_name(
            gspread_utils.AUTHORIZED_CLIENT_FILENAME
        )
        auth_user_file.touch()
        # call the function
        success, client = gspread_utils.authenticate_client(
            credentials_file=tmp_file, force_reauth=True, log=True
        )
        assert success
        assert client is not None
        # check that the file did not exist when `gspread.oauth` was
        # called
        assert not gspread_patch_oauth.auth_file_existed(0)

    @parametrize_indirect(
        {"tmp_file": ("credentials.json", "credentials")},
    )
    def test_success(self, track_no_error_logs, gspread_patch_oauth, tmp_file):
        success, client = gspread_utils.authenticate_client(
            credentials_file=tmp_file, log=True
        )
        assert success
        assert client is not None
        assert gspread_patch_oauth.times_called > 0


@parametrize(
    {"sheet_name": "test sheet"},
    {"sheet_name": "sheet name"},
    {"sheet_name": "Untitled spreadsheet"},
)
class TestOpenSpreadsheet:
    """Tests the function
    :func:`~codepost_powertools._utils.gspread_utils.open_spreadsheet`.
    """

    @pytest.fixture(name="mock_client", autouse=True)
    def fixture_mock_client(self, request):
        """Returns a MockClient object.

        Accepts the following kwargs:
            expired (bool): Whether the returned client is expired.
            spreadsheet_success (bool): Whether opening a spreadsheet is
                successful.
        """
        kwargs = get_request_param(request, default={})
        # allow the `open_spreadsheet()` method to work
        kwargs.setdefault("expired", False)
        mock_client = MockClient(**kwargs)

        def always_fail(msg):
            def fail(*args, **kwargs):
                raise RuntimeError(msg)

            return fail

        with pytest.MonkeyPatch.context() as monkeypatch:
            # patch the global variable with the mock client
            monkeypatch.setattr(gspread_utils, "_GLOBAL_CLIENT", mock_client)
            # don't allow `authenticate_client()` to be called
            monkeypatch.setattr(
                gspread_utils,
                "authenticate_client",
                always_fail("`authenticate_client()` should not be called"),
            )
            yield mock_client

    @parametrize_indirect(
        {"mock_client": {"spreadsheet_success": False}},
    )
    def test_error(self, track_logs, sheet_name):
        # check exception
        with pytest.raises(
            gspread.SpreadsheetNotFound, match=SPREADSHEET_NOT_FOUND_ERROR
        ):
            gspread_utils.open_spreadsheet(sheet_name, log=False)
        # check logs
        track_logs.reset("ERROR")
        success, spreadsheet = gspread_utils.open_spreadsheet(
            sheet_name, log=True
        )
        assert not success
        assert spreadsheet is None
        assert track_logs.saw_msg_logged("ERROR", SPREADSHEET_NOT_FOUND_ERROR)

    @parametrize_indirect(
        {"mock_client": {"spreadsheet_success": True}},
    )
    def test_no_error(self, track_no_error_logs, sheet_name):
        success, spreadsheet = gspread_utils.open_spreadsheet(
            sheet_name, log=True
        )
        assert success
        assert spreadsheet is not None
