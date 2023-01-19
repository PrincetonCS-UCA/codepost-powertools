"""
Utilities for reading and writing files.
"""

# =============================================================================

from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

import comma

from codepost_powertools._utils import _get_logger, handle_error
from codepost_powertools.utils.codepost_utils import course_str
from codepost_powertools.utils.cptypes import Assignment, Course
from codepost_powertools.utils.types import (
    PathLike,
    SuccessOrErrorMsg,
    SuccessOrNone,
)

# =============================================================================

DEFAULT_OUTPUT_FOLDER = "output"

DEFAULT_EXTS = (
    ".txt",
    ".csv",
)

# =============================================================================


def get_path(
    start_dir: PathLike = DEFAULT_OUTPUT_FOLDER,
    *,
    filename: Optional[PathLike] = None,
    course: Optional[Course] = None,
    assignment: Optional[Assignment] = None,
    folder: Optional[PathLike] = None,
    log: bool = False,
) -> SuccessOrNone[Path]:
    """Gets the path ``"[start_dir]/[course]/[assignment]/[folder]/[file]"``.

    If any part is not given, it will not be included. If ``course`` is
    not given, ``assignment`` will not be included either.

    Args:
        start_dir (|PathLike|): The starting directory.
        filename (|PathLike|): The file.
        course (|Course|_): The course.
        assignment (|Assignment|_): The assignment.
        folder (|PathLike|): The output folder.
        log (|bool|): Whether to show log messages.

    Returns:
        |SuccessOrNone| [|Path|]: The resulting path.

    Raises:
        NotADirectoryError: If ``start_dir`` exists and is not a
            directory.

    .. versionadded:: 0.1.0
    .. versionchanged:: 0.1.1
       ``start_dir`` does not need to exist.
    """
    _logger = _get_logger(log)

    result = Path(start_dir)
    if result.exists() and not result.is_dir():
        handle_error(log, NotADirectoryError, "Not a directory: {}", start_dir)
        return False, None

    if course is not None:
        result = result / course_str(course, delim="_")
        if assignment is not None:
            result = result / assignment.name
    elif assignment is not None:
        _logger.warning(
            "Assignment ({!r}) will not be included: course was not given",
            assignment.name,
        )

    if folder is not None:
        result = result / folder

    if filename is not None:
        result = result / filename

    return True, result


# =============================================================================


def validate_csv_silent(filepath: PathLike) -> SuccessOrErrorMsg:
    """Validates that the given filepath has a ``".csv"`` extension.

    Args:
        filepath (|PathLike|): The filepath.

    Returns:
        |SuccessOrErrorMsg|:
            Whether the given filepath is a csv file, and an error
            message if not.

    .. versionadded:: 0.1.0
    """
    path = Path(filepath)
    if path.suffix != ".csv":
        return False, f"Not a csv file: {filepath}"
    return True, None


def validate_csv(filepath: PathLike, *, log: bool = False) -> bool:
    """Validates that the given filepath has a ``".csv"`` extension.

    Args:
        filepath (|PathLike|): The filepath.
        log (|bool|): Whether to show log messages.

    Returns:
        |bool|: Whether the given filepath is a csv file.

    Raises:
        ValueError: If ``filepath`` is not a csv file.

    .. versionadded:: 0.1.0
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
) -> bool:
    """Saves data into a csv file.

    Args:
        data (``Iterable[Mapping[str, Any]]``): The data.
            Each element in the iterable should be a mapping from the
            column name to the value. Each mapping object should have
            all the keys of the resulting csv file.
        filepath (|PathLike|): The path of the csv file.
        description (|str|): The description of the log message.
        log (|bool|): Whether to show log messages.

    Returns:
        |bool|: Whether the data was successfully saved.

    Raises:
        ValueError: If ``filepath`` is not a csv file.
    """
    _logger = _get_logger(log)

    success = validate_csv(filepath, log=log)
    if not success:
        return False

    _logger.info("Saving {} to: {}", description, filepath)

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    comma.dump(data, filepath)
    return True
