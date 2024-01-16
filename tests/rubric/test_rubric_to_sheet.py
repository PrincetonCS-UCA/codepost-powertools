"""
Tests the ``export`` command.
"""

# =============================================================================

import pytest

from codepost_powertools.rubric import rubric_to_sheet
from tests._utils.conftest import (  # Importing fixtures; pylint: disable=unused-import
    fixture_mock_get_path,
    fixture_mock_get_path_not_called,
    fixture_mock_open_spreadsheet,
    fixture_mock_save_csv,
    fixture_mock_save_csv_not_called,
    fixture_mock_validate_csv,
    fixture_mock_validate_csv_not_called,
)
from tests.helpers import parametrize, parametrize_indirect
from tests.mocks import (
    MockAssignment,
    MockCourse,
    MockRubricCategory,
    MockRubricComment,
    MockWorksheet,
)
from tests.utils.conftest import (  # Importing fixtures; pylint: disable=unused-import
    fixture_mock_get_assignment,
    fixture_mock_get_course,
    fixture_mock_get_course_roster,
    fixture_mock_get_course_roster_not_called,
    fixture_mock_with_course,
)

# =============================================================================

NO_ASSIGNMENTS_ERROR = r"No assignments to export"
ASSIGNMENT_NOT_FOUND_ERROR = r"Assignment .+ not found in the course"
FOUND_WORKSHEETS_DEBUG = r"[Ff]ound \d+ worksheet"
CREATED_WORKSHEETS_DEBUG = r"[Cc]reated \d+ worksheet"
MULTIPLE_WORKSHEETS_WARNING = r"Multiple worksheets for assignment id"
REPLACING_WORKSHEET_DEBUG = r"Replacing worksheet .+ for assignment .+"

# =============================================================================

MOCK_RUBRIC = [
    MockRubricCategory(
        name="Category1",
        comments=[
            MockRubricComment(
                name="comment1",
                point_delta=-1,
                text="comment text",
                explanation="comment explanation",
                instructions="comment instructions",
                is_template=True,
            ),
            MockRubricComment(
                name="comment2",
                point_delta=1,
                text="COMMENT TEXT",
                explanation="COMMENT EXPLANATION",
                instructions="COMMENT INSTRUCTIONS",
                is_template=False,
            ),
        ],
    ),
    MockRubricCategory(
        name="Category2",
        comments=[
            MockRubricComment(name="comment3", point_delta=0),
            MockRubricComment(name="comment4", point_delta=0),
        ],
    ),
]

# =============================================================================


def _check_all(successes, expected):
    return all(success is expected for success in successes.values())


def all_failures(successes):
    return _check_all(successes, False)


def all_successes(successes):
    return _check_all(successes, True)


def check_failures(successes, *failures):
    failures = frozenset(failures)
    return all(
        success != (assignment_name in failures)
        for assignment_name, success in successes.items()
    )


# =============================================================================

# Use this fixture in all tests
pytestmark = pytest.mark.usefixtures("mock_with_course")

# =============================================================================


@parametrize_indirect({"mock_with_course": {"success": False}})
@parametrize(
    {"course_tuple": ("Course", "F2022")},
    {"course_tuple": ("Some Course", "Period")},
    {"course_tuple": ("", "")},
)
@parametrize(
    {
        "sheet_name": "Sheet",
        "assignments": [],
    }
)
def test_course_retrieval_failed(
    track_no_error_logs,
    track_logs,
    mock_with_course,
    course_tuple,
    sheet_name,
    assignments,
):
    track_logs.reset("INFO")
    successes = rubric_to_sheet.export_rubric(
        course_tuple, sheet_name, assignments, log=True
    )
    # course retrieval failed, so nothing should be successful
    assert all_failures(successes)
    # course retrieval failed, so there should be no logs
    assert not track_logs.saw_level_logged("INFO")


@parametrize(
    {"course_obj": MockCourse(name="Course", assignments=[])},
    {
        "course_obj": MockCourse(
            assignments=[
                MockAssignment(1, "Assignment1"),
                MockAssignment(2, "Assignment2"),
            ],
        )
    },
)
@parametrize({"assignments": []})
def test_no_assignments_given(track_logs, course_obj, assignments):
    # doesn't really matter for this test
    sheet_name = "Sheet"
    track_logs.reset("ERROR")
    successes = rubric_to_sheet.export_rubric(
        course_obj, sheet_name, assignments, log=True
    )
    assert len(successes) == 0
    assert track_logs.saw_msg_logged("ERROR", NO_ASSIGNMENTS_ERROR, exact=True)


@parametrize(
    {"course_obj": MockCourse(name="Course", assignments=[])},
    {
        "course_obj": MockCourse(
            assignments=[
                MockAssignment(1, "Assignment1"),
                MockAssignment(2, "Assignment2"),
            ],
        )
    },
)
@parametrize(
    {
        "assignments": [
            "Unknown Assignment",
            "New Assignment",
        ]
    }
)
def test_all_assignments_not_found(track_logs, course_obj, assignments):
    # doesn't really matter for this test
    sheet_name = "Sheet"
    track_logs.reset("WARNING", "ERROR")
    successes = rubric_to_sheet.export_rubric(
        course_obj, sheet_name, assignments, log=True
    )
    assert len(successes) == len(assignments)
    assert all_failures(successes)
    assert track_logs.saw_msg_logged("WARNING", ASSIGNMENT_NOT_FOUND_ERROR)
    assert track_logs.saw_msg_logged("ERROR", NO_ASSIGNMENTS_ERROR, exact=True)


@parametrize_indirect({"mock_open_spreadsheet": {"success": False}})
@parametrize(
    {
        "course_obj": MockCourse(
            assignments=[
                MockAssignment(1, "Assignment1"),
                MockAssignment(2, "Assignment2"),
            ],
        )
    }
)
@parametrize(
    {
        "assignments": [
            "Assignment1",
            "Assignment2",
            "Unknown Assignment",
            "",
        ],
        "num_found": 2,
    },
    {
        "assignments": [
            "Assignment1",
            "Test Assignment",
        ],
        "num_found": 1,
    },
)
def test_found_some_but_not_all_assignments(
    track_logs,
    mock_open_spreadsheet,
    course_obj,
    assignments,
    num_found,
):
    # doesn't really matter for this test, as long as it fails
    sheet_name = "Sheet"
    track_logs.reset("INFO", "WARNING")
    successes = rubric_to_sheet.export_rubric(
        course_obj, sheet_name, assignments, log=True
    )
    assert len(successes) == len(assignments)
    assert all_failures(successes)
    assert track_logs.saw_msg_logged("WARNING", ASSIGNMENT_NOT_FOUND_ERROR)
    # not including the "s" of "assignments" in case only 1 is found
    assert track_logs.saw_msg_logged("INFO", f"Found {num_found} assignment")


@parametrize(
    {
        "course_obj": MockCourse(
            assignments=[
                MockAssignment(1, "Assignment1", categories=MOCK_RUBRIC),
            ]
        ),
        "assignments": ["Assignment1"],
    },
    {
        "course_obj": MockCourse(
            assignments=[
                MockAssignment(1, "Assignment1", categories=MOCK_RUBRIC),
                MockAssignment(2, "Assignment2", categories=MOCK_RUBRIC),
            ]
        ),
        "assignments": ["Assignment1", "Assignment2"],
    },
)
class TestRubricExported:
    """Tests that ensure the assignment rubrics were exported."""

    @staticmethod
    def add_worksheets(spreadsheet):
        spreadsheet.add_mock_worksheets(
            [MockWorksheet(spreadsheet, "Existing worksheet")]
        )

    @parametrize_indirect(
        {"mock_open_spreadsheet": {"success": True, "setup": add_worksheets}}
    )
    def test_rubric_exported(
        self,
        track_no_error_logs,
        track_logs,
        mock_open_spreadsheet,
        course_obj,
        assignments,
    ):
        # doesn't matter
        sheet_name = "Sheet"
        track_logs.reset("DEBUG")
        successes = rubric_to_sheet.export_rubric(
            course_obj, sheet_name, assignments, log=True
        )
        assert len(successes) == len(assignments)
        assert all_successes(successes)
        # since no options were given, all the worksheets must have been
        # created, not found
        assert track_logs.saw_msg_logged("DEBUG", CREATED_WORKSHEETS_DEBUG)
        assert not track_logs.saw_msg_logged("DEBUG", FOUND_WORKSHEETS_DEBUG)
        spreadsheet = mock_open_spreadsheet.get_last_spreadsheet()
        assert spreadsheet.times_called("add_worksheet") >= len(assignments)
        # started with 1 worksheet
        assert spreadsheet.num_worksheets() == 1 + len(assignments)


# If `wipe` is true, `replace` has no effect
@parametrize({"replace": False}, {"replace": True})
class TestWipe:
    """Tests that wipe the entire spreadsheet."""

    # TODO


@parametrize(
    {
        "course_obj": MockCourse(
            assignments=[
                # Make sure any assignment id and name changes here are
                # reflected in the spreadsheet setup functions below
                MockAssignment(1, "Assignment1", categories=MOCK_RUBRIC),
                MockAssignment(2, "Assignment2", categories=MOCK_RUBRIC),
            ]
        ),
        "assignments": ["Assignment1", "Assignment2"],
    }
)
class TestReplace:
    """Tests that replace existing worksheets."""

    @staticmethod
    def _worksheet_with_id(spreadsheet, assignment_id, title=None):
        if title is None:
            title = f"Assignment{assignment_id}"
        return MockWorksheet(spreadsheet, title, values=[[assignment_id]])

    @staticmethod
    def all_existing_worksheets(spreadsheet):
        """Adds one worksheet for each assignment to the spreadsheet."""
        worksheets = []
        for assignment_id in (1, 2):
            worksheets.append(
                TestReplace._worksheet_with_id(spreadsheet, assignment_id)
            )
        spreadsheet.add_mock_worksheets(worksheets)

    @staticmethod
    def multiple_existing_worksheets(spreadsheet):
        """Adds at least one worksheet for each assignment to the
        spreadsheet.
        """
        worksheets = []
        for assignment_id, title in (
            (1, "Assignment1"),
            (1, "Assignment1 again"),
            (2, "Assignment2"),
        ):
            worksheets.append(
                TestReplace._worksheet_with_id(
                    spreadsheet, assignment_id, title
                )
            )
        spreadsheet.add_mock_worksheets(worksheets)

    @staticmethod
    def one_existing_worksheet(spreadsheet):
        """Adds a worksheet for one assignment to the spreadsheet."""
        assignment_id = 1
        spreadsheet.add_mock_worksheets(
            [TestReplace._worksheet_with_id(spreadsheet, assignment_id)]
        )

    @staticmethod
    def no_existing_worksheets(spreadsheet):
        """Adds worksheets that don't correspond with any assignments to
        the spreadsheet.
        """
        spreadsheet.add_mock_worksheets(
            [MockWorksheet(spreadsheet, "Assignment")]
        )

    @parametrize_indirect(
        {
            "mock_open_spreadsheet": {
                "success": True,
                "setup": all_existing_worksheets,
            }
        }
    )
    def test_all_existing_worksheets(
        self,
        track_no_error_logs,
        track_logs,
        mock_open_spreadsheet,
        course_obj,
        assignments,
    ):
        # doesn't matter
        sheet_name = "Sheet"
        track_logs.reset("DEBUG")
        successes = rubric_to_sheet.export_rubric(
            course_obj, sheet_name, assignments, replace=True, log=True
        )
        assert len(successes) == len(assignments)
        assert all_successes(successes)
        assert track_logs.saw_msg_logged("DEBUG", REPLACING_WORKSHEET_DEBUG)
        assert track_logs.saw_msg_logged("DEBUG", FOUND_WORKSHEETS_DEBUG)
        spreadsheet = mock_open_spreadsheet.get_last_spreadsheet()
        # the worksheets were replaced, so they must have been deleted
        # and added
        # if the TODO at rubric_to_sheet:453 is resolved, these two
        # lines might fail
        assert spreadsheet.times_called("del_worksheet") >= len(assignments)
        assert spreadsheet.times_called("add_worksheet") >= len(assignments)
        # all existing worksheets were replaced
        assert spreadsheet.num_worksheets() == len(assignments)

    @parametrize_indirect(
        {
            "mock_open_spreadsheet": {
                "success": True,
                "setup": multiple_existing_worksheets,
            }
        }
    )
    def test_multiple_existing_worksheets(
        self,
        track_no_error_logs,
        track_logs,
        mock_open_spreadsheet,
        course_obj,
        assignments,
    ):
        # doesn't matter
        sheet_name = "Sheet"
        track_logs.reset("DEBUG", "WARNING")
        successes = rubric_to_sheet.export_rubric(
            course_obj, sheet_name, assignments, replace=True, log=True
        )
        assert len(successes) == len(assignments)
        assert all_successes(successes)
        assert track_logs.saw_msg_logged("DEBUG", REPLACING_WORKSHEET_DEBUG)
        assert track_logs.saw_msg_logged(
            "WARNING", MULTIPLE_WORKSHEETS_WARNING
        )
        spreadsheet = mock_open_spreadsheet.get_last_spreadsheet()
        # the worksheets were replaced, so they must have been deleted
        # and added
        # if the TODO at rubric_to_sheet:453 is resolved, these two
        # lines might fail
        assert spreadsheet.times_called("del_worksheet") >= len(assignments)
        assert spreadsheet.times_called("add_worksheet") >= len(assignments)
        # two existing worksheets were replaced, while one of them was a
        # duplicate for an assignment
        assert spreadsheet.num_worksheets() == len(assignments) + 1

    @parametrize_indirect(
        {
            "mock_open_spreadsheet": {
                "success": True,
                "setup": one_existing_worksheet,
            }
        }
    )
    def test_one_existing_worksheet(
        self,
        track_no_error_logs,
        track_logs,
        mock_open_spreadsheet,
        course_obj,
        assignments,
    ):
        # doesn't matter
        sheet_name = "Sheet"
        track_logs.reset("DEBUG")
        successes = rubric_to_sheet.export_rubric(
            course_obj, sheet_name, assignments, replace=True, log=True
        )
        assert len(successes) == len(assignments)
        assert all_successes(successes)
        assert track_logs.saw_msg_logged("DEBUG", REPLACING_WORKSHEET_DEBUG)
        # one worksheet was replaced and one worksheet was created, so
        # both messages should be logged
        assert track_logs.saw_msg_logged("DEBUG", FOUND_WORKSHEETS_DEBUG)
        assert track_logs.saw_msg_logged("DEBUG", CREATED_WORKSHEETS_DEBUG)

    @parametrize_indirect(
        {
            "mock_open_spreadsheet": {
                "success": True,
                "setup": no_existing_worksheets,
            }
        }
    )
    def test_no_existing_worksheets(
        self,
        track_no_error_logs,
        track_logs,
        mock_open_spreadsheet,
        course_obj,
        assignments,
    ):
        # doesn't matter
        sheet_name = "Sheet"
        track_logs.reset("DEBUG")
        successes = rubric_to_sheet.export_rubric(
            course_obj, sheet_name, assignments, replace=True, log=True
        )
        assert len(successes) == len(assignments)
        assert all_successes(successes)
        assert not track_logs.saw_msg_logged(
            "DEBUG", REPLACING_WORKSHEET_DEBUG
        )
        # all worksheets were created
        assert not track_logs.saw_msg_logged("DEBUG", FOUND_WORKSHEETS_DEBUG)
        assert track_logs.saw_msg_logged("DEBUG", CREATED_WORKSHEETS_DEBUG)
        spreadsheet = mock_open_spreadsheet.get_last_spreadsheet()
        # started with 1 worksheet that wasn't replaced
        assert spreadsheet.num_worksheets() == 1 + len(assignments)


class TestCountInstances:
    """Tests that count the instances of rubric comments."""

    # TODO
