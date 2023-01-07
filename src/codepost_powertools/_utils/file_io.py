"""
file_io.py
Utilities for reading and writing files.
"""

# =============================================================================

from pathlib import Path
from typing import Any, Iterable, Mapping

import comma

from codepost_powertools._utils import _get_logger, handle_error
from codepost_powertools._utils.types import (
    PathLike,
    SuccessOrErrorMsg,
    SuccessOrNone,
)
from codepost_powertools.utils.codepost_utils import course_str
from codepost_powertools.utils.cptypes import Assignment, Course

# =============================================================================

OUTPUT_FOLDER = Path("output")

DEFAULT_EXTS = (
    ".txt",
    ".csv",
)

# =============================================================================


def get_path(
    start_dir: PathLike = ".",
    *,
    filename: PathLike = None,
    course: Course = None,
    assignment: Assignment = None,
    folder: PathLike = None,
    log: bool = False,
) -> SuccessOrNone[Path]:
    """Gets the path "[course]/[assignment]/[folder]/[file]".

    If `course` is None, `assignment` will not be included.

    Args:
        start_dir (PathLike): The starting directory.
        filename (PathLike): The file.
        course (Course): The course.
        assignment (Assignment): The assignment.
        folder (PathLike): The output folder.
        log (bool): Whether to show log messages.

    Returns:
        SuccessOrNone[Path]: The resulting path.

    Raises:
        FileNotFoundError: If `start_dir` does not exist.
        NotADirectoryError: If `start_dir` is not a directory.
    """
    _logger = _get_logger(log)

    result = Path(start_dir)
    if not result.exists():
        handle_error(
            log,
            FileNotFoundError,
            "Starting directory does not exist: {}",
            start_dir,
        )
        return False, None
    if not result.is_dir():
        handle_error(log, NotADirectoryError, str(start_dir))
        return False, None

    if course is not None:
        result = result / course_str(course, delim="_")
        if assignment is not None:
            result = result / assignment.name
    elif assignment is not None:
        _logger.warning(
            "Assignment ({!r}) will not be included: course was not given",
            assignment,
        )

    if folder is not None:
        result = result / folder

    if filename is not None:
        result = result / filename

    return True, result


# =============================================================================


def validate_csv_silent(filepath: PathLike) -> SuccessOrErrorMsg:
    """Validates that the given filepath has a ".csv" extension.

    Args:
        filepath (PathLike): The filepath.

    Returns:
        SuccessOrErrorMsg: Whether the given filepath is a csv file, and
            an error message if not.
    """
    path = Path(filepath)
    if path.suffix != ".csv":
        return False, f"Not a csv file: {filepath}"
    return True, None


def validate_csv(filepath: PathLike, *, log: bool = False) -> bool:
    """Validates that the given filepath has a ".csv" extension.

    Args:
        filepath (PathLike): The filepath.
        log (bool): Whether to show log messages.

    Returns:
        bool: Whether the given filepath is a csv file.

    Raises:
        ValueError: If `filepath` is not a csv file.
    """
    success, error_msg = validate_csv_silent(filepath)
    if not success:
        handle_error(log, ValueError, error_msg)
    return success


def save_csv(
    data: Iterable[Mapping[str, Any]],
    filepath: PathLike,
    *,
    description: str = "data",
    log: bool = False,
):
    """Saves data into a csv file.

    If `filepath` is not a csv file, does nothing.

    Args:
        data (Iterable[Mapping[str, Any]]): The data.
        filepath (PathLike): The path of the csv file.
        description (str): The description of the log message.
        log (bool): Whether to show log messages.

    Raises:
        ValueError: If `filepath` is not a csv file.
    """
    _logger = _get_logger(log)

    success = validate_csv(filepath, log=log)
    if not success:
        return

    _logger.info("Saving {} to: {}", description, filepath)

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    comma.dump(data, filepath)
