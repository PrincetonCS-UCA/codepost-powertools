"""
Utilities involving the codePost SDK.
"""

# =============================================================================

import functools
import re
from typing import Optional

import codepost

from codepost_powertools._utils import _get_logger, handle_error
from codepost_powertools.utils.cptypes import (
    Assignment,
    Course,
    Roster,
    isinstance_cp,
)
from codepost_powertools.utils.types import (
    AssignmentArg,
    CourseArg,
    SuccessOrNone,
)

# =============================================================================

__all__ = (
    "TIER_FORMAT",
    "TIER_PATTERN",
    "get_course",
    "course_str",
    "get_course_roster",
    "get_assignment",
)

# =============================================================================

# Tier format constants (specific to Princeton COS126)
TIER_FORMAT = "\\[T{tier}\\] {text}"
TIER_PATTERN = re.compile(r"\\\[T(?P<tier>\d+)\\] (?P<text>.*)")

# =============================================================================


def with_course(func):
    """Decorates a function to fetch a course before calling.

    This decorator will fetch a |Course|_ if necessary to call the
    decorated function.

    .. code-block:: python

       func(course: CourseArg, *args, **kwargs) -> RT
       # becomes
       func(course: Course | None, *args, **kwargs) -> RT

    If the retrieval is unsuccessful, ``course`` will be passed as
    ``None``, which the function should handle itself.

    .. versionadded:: 0.1.0
    """

    @functools.wraps(func)
    def wrapped(course: CourseArg, *args, **kwargs):
        log = kwargs.get("log", False)
        if not isinstance_cp(course, Course):
            # `course` is a tuple of the course name and period
            name, period = course
            # if this call fails, `course` will be None, which is passed
            _, course = get_course(name, period, log=log)
        return func(course, *args, **kwargs)

    return wrapped


def with_course_and_assignment(func):
    """Decorates a function to fetch a course and assignment before
    calling.

    This decorator will fetch a |Course|_ and |Assignment|_ if necessary
    to call the decorated function.

    .. code-block:: python

       func(
         course: CourseArg, assignment: AssignmentArg,
         *args, **kwargs
       ) -> RT
       # becomes
       func(
         course: Course | None, assignment: Assignment | None,
         *args, **kwargs
       ) -> RT

    If any retrievals are unsuccessful, ``course`` and ``assignment``
    will both be passed as ``None``, which the function should handle
    itself.

    .. note
       If |Course|_ and |Assignment|_ objects are given, the decorator
       will simply pass the arguments to the decorated function without
       checking that the assignment belongs to the course. This is up to
       the function to ensure.

    .. versionadded:: 0.1.0
    """

    @functools.wraps(func)
    @with_course
    def wrapped(
        course: Optional[Course], assignment: AssignmentArg, *args, **kwargs
    ):
        log: bool = kwargs.get("log", False)
        if course is None:
            # course retrieval failed; cannot get assignment
            assignment = None
        elif not isinstance_cp(assignment, Assignment):
            success, assignment = get_assignment(course, assignment, log=log)
            if not success:
                # also set `course` to None
                course = None
        return func(course, assignment, *args, **kwargs)

    return wrapped


# =============================================================================


def get_course(
    name: str, period: str, *, log: bool = False
) -> SuccessOrNone[Course]:
    """Gets a codePost course.

    If there are multiple courses with the same name and period, the
    first one found is returned.

    Args:
        name (|str|): The course name.
        period (|str|): The course period.
        log (|bool|): Whether to show log messages.

    Returns:
        |SuccessOrNone| [|Course|_]:
            The course.

    Raises:
        ValueError: If no course is found.

    .. versionadded:: 0.1.0
    """
    _logger = _get_logger(log)

    _logger.info("Getting course {!r} with period {!r}", name, period)

    # specifying the name and period in `iter_available()` works, but it
    # ignores empty strings, so do this to handle all cases
    found = []
    for course in codepost.course.iter_available():
        if course.name == name and course.period == period:
            found.append(course)
            if len(found) >= 2:
                # already found two; don't need to check rest
                break
    if len(found) > 0:
        course = found[0]
        if len(found) > 1:
            _logger.warning(
                "Multiple courses found with name {!r} and period {!r}: "
                "returning course {}",
                name,
                period,
                course.id,
            )
        return True, found[0]

    handle_error(
        log,
        ValueError,
        "No course found with name {!r} and period {!r}",
        name,
        period,
    )
    return False, None


def course_str(course: Course, *, delim: str = " ") -> str:
    """Returns a str representation of a course.

    Args:
        course (|Course|_): The course.
        delim (|str|): A delimiting string between the name and the
            period.

    Returns:
        |str|: A string representation of the course.

    .. versionadded:: 0.1.0
    """
    return f"{course.name}{delim}{course.period}"


# =============================================================================


@with_course
def get_course_roster(
    course: Course, *, log: bool = False
) -> SuccessOrNone[Roster]:
    """Gets the roster for the given course.

    Args:
        course (|CourseArg|): The course.
        log (|bool|): Whether to show log messages.

    Returns:
        |SuccessOrNone| [|Roster|_]:
            The roster.

    .. versionadded:: 0.1.0
    """
    _logger = _get_logger(log)

    if course is None:
        return False, None

    _logger.info("Getting roster for course {!r}", course_str(course))
    roster = codepost.roster.retrieve(course.id)
    return True, roster


# =============================================================================


@with_course
def get_assignment(
    course: Course, assignment_name: str, *, log: bool = False
) -> SuccessOrNone[Assignment]:
    """Gets a codePost assignment from a course.

    Args:
        course (|CourseArg|): The course.
        assignment_name (|str|): The assignment name.
        log (|bool|): Whether to show log messages.

    Returns:
        |SuccessOrNone| [|Assignment|_]:
            The assignment.

    Raises:
        ValueError: If the assignment is not found.

    .. versionadded:: 0.1.0
    .. versionchanged:: 0.2.0
       codePost does not allow multiple assignments to have the same
       name, so the extra checks for that were removed.
    """
    _logger = _get_logger(log)

    if course is None:
        return False, None

    _logger.info("Getting assignment {!r}", assignment_name)

    for assignment in course.assignments:
        if assignment.name == assignment_name:
            return True, assignment

    handle_error(log, ValueError, "Assignment {!r} not found", assignment_name)
    return False, None
