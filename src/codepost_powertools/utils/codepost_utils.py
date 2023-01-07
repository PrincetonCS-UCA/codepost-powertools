"""
codepost_utils.py
Utilities involving the codePost SDK.
"""

# =============================================================================

import functools
from typing import Optional

import codepost

from codepost_powertools._utils import _get_logger, handle_error
from codepost_powertools._utils.types import (
    AssignmentArg,
    CourseArg,
    SuccessOrNone,
)
from codepost_powertools.utils.cptypes import (
    Assignment,
    Course,
    Roster,
    isinstance_cp,
)

# =============================================================================

__all__ = (
    "get_course",
    "course_str",
    "get_course_roster",
    "get_assignment",
)

# =============================================================================


def with_course(func):
    """Decorates a function to fetch a course before calling.

    If the retrieval is unsuccessful, `None` will be passed to the
    function, where it should handle that case accordingly.
    """

    @functools.wraps(func)
    def wrapped(course: CourseArg, *args, **kwargs):
        log = kwargs.get("log", False)
        if not isinstance_cp(course, Course):
            # `course` is a tuple of the course name and period
            name, period = course
            # if this call fails, `course` will be None, which gets
            # passed
            _, course = get_course(name, period, log=log)
        return func(course, *args, **kwargs)

    return wrapped


def with_course_and_assignment(func):
    """Decorates a function to fetch a course and assignment before
    calling.

    If the retrievals are unsuccessful, `None` will be passed to the
    function, where it should handle that case accordingly.
    """

    @functools.wraps(func)
    @with_course
    def wrapped(
        course: Optional[Course], assignment: AssignmentArg, *args, **kwargs
    ):
        log = kwargs.get("log", False)
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

    If there are courses with the same name and period, the first one
    found is returned.

    Args:
        name (str): The course name.
        period (str): The course period.
        log (bool): Whether to show log messages.

    Returns:
        SuccessOrNone[Course]: The course.

    Raises:
        ValueError: If no course is found.
    """
    _logger = _get_logger(log)

    _logger.info("Getting course {!r} with period {!r}", name, period)

    # specifying the name and period in `list_available()` works, but it
    # ignores empty strings, so do this to handle all cases
    for course in codepost.course.list_available():
        if course.name == name and course.period == period:
            return True, course

    handle_error(
        log,
        ValueError,
        "No course found with name {!r} and period {!r}",
        name,
        period,
    )
    return False, None


def course_str(course: Course, delim: str = " ") -> str:
    """Returns a str representation of a course.

    Args:
        course (Course): The course.
        delim (str): A deliminating str between the name and the period.
    """
    return f"{course.name}{delim}{course.period}"


# =============================================================================


@with_course
def get_course_roster(
    course: Course, *, log: bool = False
) -> SuccessOrNone[Roster]:
    """Gets the roster for the given course.

    Args:
        course (CourseArg): The course.
        log (bool): Whether to show log messages.

    Returns:
        SuccessOrNone[Roster]: The roster.
    """
    _logger = _get_logger(log)

    if course is None:
        return False, None

    _logger.info("Getting roster for course {!r}", course_str(course))
    roster = codepost.roster.retrieve(course.id)
    return True, roster


# =============================================================================


def get_assignment(
    course: Course, assignment_name: str, *, log: bool = False
) -> SuccessOrNone[Assignment]:
    """Gets a codePost assignment from a course.

    Args:
        course (Course): The course.
        assignment_name (str): The assignment name.
        log (bool): Whether to show log messages.

    Returns:
        SuccessOrNone[Assignment]: The assignment.

    Raises:
        ValueError: If the assignment is not found.
    """
    _logger = _get_logger(log)

    _logger.info("Getting assignment {!r}", assignment_name)

    for assignment in course.assignments:
        if assignment.name == assignment_name:
            return True, assignment

    handle_error(log, ValueError, "Assignment {!r} not found", assignment_name)
    return False, None
