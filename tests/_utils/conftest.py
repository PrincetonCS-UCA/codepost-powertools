"""
Fixtures for the ``_utils`` private utilities.

These fixtures mock the utility functions themselves; they are not used
in the tests for the utilities.

These fixtures are available for use in tests outside of this
subpackage. However, due to the way ``pytest`` works, any other test
files that want to use the fixtures in this file must import all the
dependencies of those fixtures as well, so that they're defined in the
scope of the calling file.

Fixtures defined:
- mock_get_path
  - mock_get_path_not_called
- mock_validate_csv_silent
- mock_validate_csv
  - mock_validate_csv_not_called
- mock_save_csv
  - mock_save_csv_not_called
- mock_authenticate_client
- mock_open_spreadsheet

``handle_error()`` does not have a mock fixture.
"""

# =============================================================================

import pytest

from codepost_powertools._utils import file_io, gspread_utils
from tests.helpers import (
    MockFunction,
    get_request_param,
    patch_with_default_module,
)
from tests.mocks import MockClient, MockSpreadsheet

patch_file_io_mock_func = patch_with_default_module(file_io)
patch_gspread_utils_mock_func = patch_with_default_module(gspread_utils)

# =============================================================================


class MockGetPath(MockFunction):
    """A mock for the ``get_path()`` function."""

    def __init__(self, success=False, filepath="testing"):
        super().__init__(enable_set=True)
        self._success = success
        self._filepath = filepath

    def mock(
        self,
        start_dir=".",
        filename=None,
        course=None,
        assignment=None,
        folder=None,
        log=False,
    ):
        if not self._success:
            # mock a failure
            return False, None
        # mock a success
        return True, self._filepath


@pytest.fixture(name="mock_get_path")
def fixture_mock_get_path(request):
    """Creates a mock for the ``get_path()`` function.

    Accepts the following kwargs:
        success (bool): Whether the path construction is successful.
        filepath (str | Path): The returned path.
    """
    kwargs = get_request_param(request, default={})
    mock_func = MockGetPath(**kwargs)
    with pytest.MonkeyPatch.context() as monkeypatch:
        patch_file_io_mock_func(monkeypatch, request, "get_path", mock_func)
        yield mock_func


@pytest.fixture(name="mock_get_path_not_called")
def fixture_mock_get_path_not_called(mock_get_path):
    """A convenience fixture for mocking the ``get_path()`` function to
    always fail, then checking that it was never called.
    """
    mock_get_path.set(success=False)
    yield mock_get_path
    assert mock_get_path.times_called == 0


# =============================================================================


class MockValidateCsvSilent(MockFunction):
    """A mock for the ``validate_csv_silent()`` function."""

    def __init__(self, success=False, error_msg="Error"):
        super().__init__(enable_set=True)
        self._success = success
        self._error_msg = error_msg

    def mock(self, filepath):
        if not self._success:
            # mock a failure
            return False, self._error_msg
        # mock a success
        return True, None


@pytest.fixture(name="mock_validate_csv_silent")
def fixture_mock_validate_csv_silent(request):
    """Creates a mock for the ``validate_csv_silent()`` function.

    Accepts the following kwargs:
        success (bool): Whether the validation is successful.
        error_msg (str): An error message to return.
    """
    kwargs = get_request_param(request, default={})
    mock_func = MockValidateCsvSilent(**kwargs)
    with pytest.MonkeyPatch.context() as monkeypatch:
        patch_file_io_mock_func(
            monkeypatch, request, "validate_csv_silent", mock_func
        )
        yield mock_func


# =============================================================================


class MockValidateCsv(MockFunction):
    """A mock for the ``validate_csv()`` function."""

    def __init__(self, success=False):
        super().__init__(enable_set=True)
        self._success = success

    def mock(self, filepath, log=False):
        return self._success


@pytest.fixture(name="mock_validate_csv")
def fixture_mock_validate_csv(request):
    """Creates a mock for the ``validate_csv()`` function.

    Accepts the following kwargs:
        success (bool): Whether the validation is successful.
    """
    kwargs = get_request_param(request, default={})
    mock_func = MockValidateCsv(**kwargs)
    with pytest.MonkeyPatch.context() as monkeypatch:
        patch_file_io_mock_func(
            monkeypatch, request, "validate_csv", mock_func
        )
        yield mock_func


@pytest.fixture(name="mock_validate_csv_not_called")
def fixture_mock_validate_csv_not_called(mock_validate_csv):
    """A convenience fixture for mocking the ``validate_csv()`` function
    to always fail, then checking that it was never called.
    """
    mock_validate_csv.set(success=False)
    yield mock_validate_csv
    assert mock_validate_csv.times_called == 0


# =============================================================================


class MockSaveCsv(MockFunction):
    """A mock for the ``save_csv()`` function."""

    def __init__(self, success=False):
        super().__init__(enable_set=True)
        self._success = success
        self.__saved_files = set()

    def mock(self, data, filepath, description="data", log=False):
        if not self._success:
            # mock a failure
            return False
        # mock a success
        self.__saved_files.add(filepath)
        return True

    def file_saved(self, filepath):
        return filepath in self.__saved_files


@pytest.fixture(name="mock_save_csv")
def fixture_mock_save_csv(request):
    """Creates a mock for the ``save_csv()`` function.

    Accepts the following kwargs:
        success (bool): Whether the save is successful.
    """
    kwargs = get_request_param(request, default={})
    mock_func = MockSaveCsv(**kwargs)
    with pytest.MonkeyPatch.context() as monkeypatch:
        patch_file_io_mock_func(monkeypatch, request, "save_csv", mock_func)
        yield mock_func


@pytest.fixture(name="mock_save_csv_not_called")
def fixture_mock_save_csv_not_called(mock_save_csv):
    """A convenience fixture for mocking the ``save_csv()`` function to
    always fail, then checking that it was never called.
    """
    mock_save_csv.set(success=False)
    yield mock_save_csv
    assert mock_save_csv.times_called == 0


# =============================================================================


class MockAuthenticateClient(MockFunction):
    """A mock for the ``authenticate_client()`` function."""

    def __init__(self, success=False, expired=True, spreadsheet_success=False):
        super().__init__(enable_set=True)
        self._success = success
        self._expired = expired
        self._spreadsheet_success = spreadsheet_success

    def mock(self, credentials_file=None, force_reauth=False, log=False):
        if not self._success:
            # mock a failure
            return False, None
        # mock a success
        return True, MockClient(
            expired=self._expired,
            spreadsheet_success=self._spreadsheet_success,
        )


@pytest.fixture(name="mock_authenticate_client")
def fixture_mock_authenticate_client(request):
    """Creates a mock for the ``authenticate_client()`` function.

    Accepts the following kwargs:
        success (bool): Whether the authentication is successful.
            Set this to False if the credentials file is invalid.
        expired (bool): Whether the credentials are expired.
        spreadsheet_success (bool): Whether spreadsheets are found with
            the ``open()`` method.
    """
    kwargs = get_request_param(request, default={})
    mock_func = MockAuthenticateClient(**kwargs)
    with pytest.MonkeyPatch.context() as monkeypatch:
        patch_gspread_utils_mock_func(
            monkeypatch, request, "authenticate_client", mock_func
        )
        yield mock_func


# =============================================================================


class MockOpenSpreadsheet(MockFunction):
    """A mock for the ``open_spreadsheet()`` function."""

    def __init__(self, success=False, setup=None):
        super().__init__(enable_set=True)
        self._success = success
        self._setup = setup
        self.__last_spreadsheet = None

    def mock(self, sheet_name, log=False):
        if not self._success:
            # mock a failure
            return False, None
        # mock a success
        spreadsheet = MockSpreadsheet(sheet_name)
        if self._setup is not None:
            self._setup(spreadsheet)
        self.__last_spreadsheet = spreadsheet
        return True, spreadsheet

    def get_last_spreadsheet(self):
        return self.__last_spreadsheet


@pytest.fixture(name="mock_open_spreadsheet")
def fixture_mock_open_spreadsheet(request):
    """Creates a mock for the ``open_spreadsheet()`` function.

    Accepts the following kwargs:
        success (bool): Whether the open is successful.
        setup (Callable[[MockSpreadsheet], None]): An optional function
            that sets up the spreadsheet to be returned. The function
            should mutate the given spreadsheet.
    """
    kwargs = get_request_param(request, default={})
    mock_func = MockOpenSpreadsheet(**kwargs)
    with pytest.MonkeyPatch.context() as monkeypatch:
        patch_gspread_utils_mock_func(
            monkeypatch, request, "open_spreadsheet", mock_func
        )
        yield mock_func
