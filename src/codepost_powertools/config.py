"""
config.py
Handle package config.
"""

# =============================================================================

from pathlib import Path

import codepost

from codepost_powertools._utils import handle_error
from codepost_powertools._utils.types import PathLike
from codepost_powertools.version import __doc_url__, __version__

# =============================================================================

__all__ = ("log_in_codepost",)

# =============================================================================

# Let codePost know about this package
codepost.set_app_info(
    name=__package__ or "codepost_powertools",
    url=__doc_url__,
    version=__version__,
)

# =============================================================================

DEFAULT_CONFIG_FILE = "config.yaml"
API_KEY = "api_key"


def log_in_codepost(
    config_file: PathLike = DEFAULT_CONFIG_FILE, *, log: bool = False
) -> bool:
    """Logs in to codePost using the api key in the YAML config file.

    Args:
        config_file (PathLike): The config file to read.
        log (bool): Whether to show log messages.

    Returns:
        bool: Whether successfully logged in.

    Raises:
        FileNotFoundError: If the config file was not found.
        RuntimeError: If the config file could not be read (likely due
            to an invalid format).
        KeyError: If the YAML config file does not contain the
            `"api_key"` key.
    """

    config_file_path = Path(config_file)
    if not config_file_path.exists() or not config_file_path.is_file():
        handle_error(
            log, FileNotFoundError, "config file not found: {}", config_file
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
            "config file could not be read (likely due to invalid format): {}",
            config_file,
        )
        return False

    if API_KEY not in config:
        handle_error(
            log,
            KeyError,
            'config file does not contain "{}" key',
            API_KEY,
        )
        return False

    codepost.configure_api_key(config[API_KEY])
    return True
