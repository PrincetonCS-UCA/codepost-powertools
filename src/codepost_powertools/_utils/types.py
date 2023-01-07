"""
types.py
Type definitions and aliases.
"""

# =============================================================================

from os import PathLike as os_PathLike
from pathlib import Path
from typing import Literal, Tuple, TypeVar

import click

from codepost_powertools.utils.cptypes import Assignment, Course

# =============================================================================

# A path-like argument
PathLike = os_PathLike | str

# The course object or a tuple of course name and period
CourseArg = Course | Tuple[str, str]
# The assignment object or the assignment name
AssignmentArg = Assignment | str

# The return type of a successful function: either True and the return
# value, or False and None
T = TypeVar("T")
SuccessOrNone = Tuple[Literal[True], T] | Tuple[Literal[False], None]
# The return type of a "silent" function: either True and None, or False
# and an error message
SuccessOrErrorMsg = Tuple[Literal[True], None] | Tuple[Literal[False], str]

# =============================================================================

_SHARED_KWARGS = {"file_okay": True, "dir_okay": False, "path_type": Path}
# An input filepath given on the command line
ParamPathIn = click.Path(exists=True, readable=True, **_SHARED_KWARGS)
# An output filepath given on the command line
ParamPathOut = click.Path(exists=False, writable=True, **_SHARED_KWARGS)
