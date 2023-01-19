"""
Handle package config.
"""

# =============================================================================

from pathlib import Path

import codepost

from codepost_powertools._utils import handle_error
from codepost_powertools.info import __version__, docs_url, package_name
from codepost_powertools.utils.types import PathLike

# =============================================================================

__all__ = ("log_in_codepost",)

# =============================================================================

# Let codePost know about this package
codepost.set_app_info(name=package_name, url=docs_url, version=__version__)

# =============================================================================

DEFAULT_CONFIG_FILE = "config.yaml"
API_KEY = "api_key"


def log_in_codepost(
    config_file: PathLike = DEFAULT_CONFIG_FILE, *, log: bool = False
) -> bool:
    """Logs in to codePost using the api key in the YAML config file.

    The api key will be searched for in a field called ``"api_key"`` in
    the config file.

    Note that all the functions in this package **will not** call this
    method for you, so you should be calling it yourself at the start of
    your script. If you are using the command line, this method is
    called before each command.

    Args:
        config_file (|PathLike|): The config file to read.
        log (|bool|): Whether to show log messages.

    Returns:
        |bool|: Whether successfully logged in.

    Raises:
        FileNotFoundError: If the config file is not found.
        RuntimeError: If the config file cannot be read (likely due to
            an invalid format).
        KeyError: If the YAML config file does not contain the
            ``"api_key"`` key.
        ValueError: If the given api key is invalid.

    .. versionadded:: 0.1.0
    """

    config_file_path = Path(config_file)
    if not config_file_path.exists() or not config_file_path.is_file():
        handle_error(
            log, FileNotFoundError, "Config file not found: {}", config_file
        )
        return False

    config = codepost.read_config_file([config_file])
    if config is None:
        # probably invalid format
        # TODO: error exact reason logged by codepost function; extract
        #   it somehow?
        handle_error(
            log,
            RuntimeError,
            "Config file could not be read (likely due to invalid format): {}",
            config_file,
        )
        return False

    if API_KEY not in config:
        handle_error(
            log,
            KeyError,
            'Config file does not contain "{}" key',
            API_KEY,
        )
        return False

    cp_api_key = config[API_KEY]

    if not isinstance(cp_api_key, str):
        # if not a str, can't be an api key. passing an unhashable
        # object to `validate_api_key()` will result in a runtime error
        success = False
    else:
        success = codepost.util.config.validate_api_key(cp_api_key)
    if not success:
        handle_error(
            log, ValueError, "Config file has invalid codePost API key"
        )
        return False

    codepost.configure_api_key(cp_api_key)
    return True
