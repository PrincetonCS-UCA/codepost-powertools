"""
Utilities involving the ``gspread`` package.
"""

# =============================================================================

from pathlib import Path
from typing import Optional

import google.auth.exceptions
import gspread
from google_auth_oauthlib.flow import InstalledAppFlow

from codepost_powertools._utils import _get_logger, handle_error
from codepost_powertools.utils.types import PathLike, SuccessOrNone
from codepost_powertools.utils.worksheet import (
    Color,
    Worksheet,
    _set_worksheet_title,
    col_index_to_letter,
    col_letter_to_index,
)

# =============================================================================

__all__ = (
    "Worksheet",
    "Color",
    "col_letter_to_index",
    "col_index_to_letter",
    "authenticate_client",
    "open_spreadsheet",
    "add_worksheet",
)

# =============================================================================

DEFAULT_CREDENTIALS_FILENAME = "client_credentials.json"
AUTHORIZED_CLIENT_FILENAME = "client_authorized.json"

# =============================================================================

# To not require callers to use the authentication function, we will
# save a global client object that can be used in any function that
# needs it.
_GLOBAL_CLIENT = None

# =============================================================================


def _local_server_flow(client_config, scopes, port=0):
    """Runs an OAuth flow exactly like
    :func:`gspread.auth.local_server_flow`, except it does not force
    opening the user's browser.

    I don't like things that open browsers without warning, and a
    message will be displayed with the authentication URL, so it will
    still work.

    .. versionadded:: 0.2.0
    """
    flow = InstalledAppFlow.from_client_config(client_config, scopes)
    return flow.run_local_server(port=port, open_browser=False)


def authenticate_client(
    *,
    credentials_file: PathLike = DEFAULT_CREDENTIALS_FILENAME,
    force_reauth: bool = False,
    log: bool = False,
) -> SuccessOrNone[gspread.Client]:
    """Authenticates the OAuth Client to connect with Google Sheets.

    If the client is already authenticated (in the cached
    ``client_authorized.json`` file), nothing will happen. However, if
    ``force_reauth`` is True, the user will be forcefully
    re-authenticated.

    If the authorization has expired, it will be refreshed.

    Args:
        credentials_file (|PathLike|): A file containing the OAuth
            credentials.
        force_reauth (|bool|): Whether to force a re-authentication.
        log (|bool|): Whether to show log messages.

    Returns:
        |SuccessOrNone| [|gspread Client|]: A client.

    Raises:
        FileNotFoundError: If the credentials file was not found.
        OSError: If the credentials file is not a file.

    .. versionadded:: 0.2.0
    """
    global _GLOBAL_CLIENT  # pylint: disable=global-statement

    _logger = _get_logger(log)

    _logger.info("Authenticating OAuth Client")

    credentials_path = Path(credentials_file)
    if not credentials_path.exists():
        handle_error(
            log,
            FileNotFoundError,
            "OAuth credentials file not found: {}",
            credentials_file,
        )
        return False, None
    if not credentials_path.is_file():
        handle_error(
            log,
            OSError,
            "OAuth credentials file is not a file: {}",
            credentials_file,
        )
        return False, None

    # put the file in the same directory
    auth_user_path = credentials_path.with_name(AUTHORIZED_CLIENT_FILENAME)
    if force_reauth and auth_user_path.exists():
        # remove the cache for re-authentication
        auth_user_path.unlink()

    # by using the local server flow, the authentication cannot fail
    oauth_kwargs = {
        "credentials_filename": credentials_path,
        "authorized_user_filename": auth_user_path,
        "flow": _local_server_flow,
        "client_factory": gspread.BackoffClient,
    }
    client = gspread.oauth(**oauth_kwargs)

    # check if the client is expired
    try:
        client.list_spreadsheet_files()
    except google.auth.exceptions.RefreshError:
        _logger.warning("OAuth Client credentials expired; refreshing")
        auth_user_path.unlink()
        # try again
        client = gspread.oauth(**oauth_kwargs)

    _GLOBAL_CLIENT = client
    return True, client


# =============================================================================


def open_spreadsheet(
    sheet_name: str, *, log: bool = False
) -> SuccessOrNone[gspread.Spreadsheet]:
    """Opens a Google Spreadsheet.

    If there are multiple spreadsheets with the same name, the first one
    found is returned.

    Args:
        sheet_name (|str|): The name of the sheet to open.
        log (|bool|): Whether to show log messages.

    Returns:
        |SuccessOrNone| [|gspread Spreadsheet|]: The spreadsheet.

    Raises:
        gspread.exceptions.SpreadsheetNotFound: If the spreadsheet was
            not found.

    .. versionadded:: 0.2.0
    """
    if _GLOBAL_CLIENT is None:
        success, _ = authenticate_client(log=log)
        if not success:
            return False, None

    _logger = _get_logger(log)

    _logger.info("Opening spreadsheet {!r}", sheet_name)

    try:
        return True, _GLOBAL_CLIENT.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        pass
    handle_error(
        log,
        gspread.SpreadsheetNotFound,
        "Spreadsheet {!r} not found",
        sheet_name,
    )
    return False, None


# =============================================================================


def add_worksheet(
    sheet: gspread.Spreadsheet,
    title: str = "Sheet",
    *,
    rows: int = 1,
    cols: int = 1,
    index: Optional[int] = None,
) -> gspread.Worksheet:
    """Adds a worksheet to the given spreadsheet.

    If a worksheet already exists with the name ``title``, a number will
    be appended to the end of the title, then incremented until there is
    no longer a conflict.

    Args:
        sheet (|gspread Spreadsheet|): The spreadsheet.
        title (|str|): The worksheet title.
        rows (|int|): The number of rows.
        cols (|int|): The number of columns.
        index (|int|): The index where the worksheet should go.
            If not given, it is added to the end.

    Returns:
        |gspread Worksheet|: The worksheet.

    .. versionadded:: 0.2.0
    """
    return _set_worksheet_title(
        sheet.add_worksheet, title, rows=rows, cols=cols, index=index
    )
