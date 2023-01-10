"""
.. The autodoc ``autodata`` directive didn't work too well, and the
   comments had to look ugly in this file, so manually documenting the
   type aliases here is the easiest thing to do.

Type definitions and aliases.

.. data:: PathLike

   Alias = :class:`os.PathLike` | |str|

   A path-like argument.

.. data:: CourseArg

   Alias = |Course|_ | ``Tuple[str, str]``

   The course object, or a tuple of course name and period.

.. data:: AssignmentArg

   Alias = |Assignment|_ | |str|

   The assignment object, or the assignment name.

.. data:: SuccessOrNone
   :canonical: codepost_powertools._utils.types.SuccessOrNone

   Alias (generic ``T``) =
   ``Tuple[Literal[True], T]`` | ``Tuple[Literal[False], None]``

   The return type of a "successful" function: either True and the
   return value, or False and None. These functions usually accept a
   ``log`` parameter for whether to show log messages on failures or
   raise exceptions.

.. data:: SuccessOrErrorMsg

   Alias =
   ``Tuple[Literal[True], None]`` | ``Tuple[Literal[False], str]``

   The return type of a "silent" function: either True and None, or
   False and an error message. These functions usually *do not* accept a
   ``log`` parameter; the successful state is returned in the tuple, and
   the user can decide what to do with the error message.
"""

# =============================================================================

from os import PathLike as os_PathLike
from pathlib import Path
from typing import Literal, Tuple, TypeVar, Union

import click

from codepost_powertools.utils.cptypes import Assignment, Course

# =============================================================================

# A path-like argument
PathLike = Union[os_PathLike, str]

# The course object, or a tuple of course name and period
CourseArg = Union[Course, Tuple[str, str]]
# The assignment object, or the assignment name
AssignmentArg = Union[Assignment, str]

# The return type of a "successful" function: either True and the return
# value, or False and None
T = TypeVar("T")
SuccessOrNone = Union[Tuple[Literal[True], T], Tuple[Literal[False], None]]
# The return type of a "silent" function: either True and None, or False
# and an error message
SuccessOrErrorMsg = Union[
    Tuple[Literal[True], None], Tuple[Literal[False], str]
]

# =============================================================================

_SHARED_KWARGS = {"file_okay": True, "dir_okay": False, "path_type": Path}
# An input filepath given on the command line
ParamPathIn = click.Path(exists=True, readable=True, **_SHARED_KWARGS)
# An output filepath given on the command line
ParamPathOut = click.Path(exists=False, writable=True, **_SHARED_KWARGS)
