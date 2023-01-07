"""
cptypes.py
The codePost types.
"""

# =============================================================================

from typing import NewType

from codepost.models.assignments import Assignments
from codepost.models.comments import Comments
from codepost.models.course_rosters import CourseRosters
from codepost.models.courses import Courses
from codepost.models.file_templates import FileTemplates
from codepost.models.files import Files
from codepost.models.rubric_categories import RubricCategories
from codepost.models.rubric_comments import RubricComments
from codepost.models.sections import Sections
from codepost.models.submission_tests import SubmissionTests
from codepost.models.submissions import Submissions
from codepost.models.test_cases import TestCases
from codepost.models.test_categories import TestCategories

# =============================================================================

__all__ = (
    "Course",
    "Roster",
    "Assignment",
    "Submission",
    "File",
    "Comment",
    "Section",
    "RubricCategory",
    "RubricComment",
    "FileTemplate",
    "TestCategory",
    "TestCase",
    "SubmissionTest",
)

# =============================================================================

_CP_TYPES = {}


def _add_type(name, tp):
    type_ = NewType(name, tp)
    _CP_TYPES[type_] = tp
    return type_


Course = _add_type("Course", Courses)
Roster = _add_type("Roster", CourseRosters)
Assignment = _add_type("Assignment", Assignments)
Submission = _add_type("Submission", Submissions)
File = _add_type("File", Files)
Comment = _add_type("Comment", Comments)
Section = _add_type("Section", Sections)
RubricCategory = _add_type("RubricCategory", RubricCategories)
RubricComment = _add_type("RubricComment", RubricComments)
FileTemplate = _add_type("FileTemplate", FileTemplates)
TestCategory = _add_type("TestCategory", TestCategories)
TestCase = _add_type("TestCase", TestCases)
SubmissionTest = _add_type("SubmissionTest", SubmissionTests)

# =============================================================================


def isinstance_cp(obj, cp_type):
    """Returns whether `obj` is of type `cp_type`.

    `typing.NewType` objects cannot be used in `isinstance()`, so this
    function provides a workaround.

    See: https://github.com/python/mypy/issues/3325#issuecomment-299546004
    """
    return isinstance(obj, _CP_TYPES.get(cp_type, cp_type))
