"""
Tests the ``ids`` command.
"""

# =============================================================================

import pytest

from codepost_powertools.grading import ids
from tests._utils.conftest import (  # Importing fixtures; pylint: disable=unused-import
    fixture_mock_get_path,
    fixture_mock_get_path_not_called,
    fixture_mock_save_csv,
    fixture_mock_save_csv_not_called,
    fixture_mock_validate_csv,
    fixture_mock_validate_csv_not_called,
)
from tests.helpers import parametrize, parametrize_indirect
from tests.mocks import MockAssignment, MockCourse, MockSubmission
from tests.utils.conftest import (  # Importing fixtures; pylint: disable=unused-import
    fixture_mock_get_assignment,
    fixture_mock_get_course,
    fixture_mock_get_course_roster,
    fixture_mock_get_course_roster_not_called,
    fixture_mock_with_course,
    fixture_mock_with_course_and_assignment,
)

# =============================================================================

ASSIGNMENT_NOT_BELONG_TO_COURSE_ERROR = (
    r"Assignment .+ does not belong to course .+"
)
GETTING_ASSIGNMENT_SUBMISSIONS_INFO = r"Getting assignment submissions"
COULD_NOT_FETCH_ROSTER_WARNING = (
    r"Could not fetch roster, so not including all students"
)
NOT_SAVING_TO_FILE_WARNING = r"Not saving to a file"

# =============================================================================


def make_course_assignment_objs(submissions):
    course_obj = MockCourse(1)
    assignment_obj = MockAssignment(
        course_id=course_obj.id, submissions=submissions
    )
    return course_obj, assignment_obj


# =============================================================================

# Use this fixture in all tests
pytestmark = pytest.mark.usefixtures("mock_with_course_and_assignment")

# =============================================================================


@parametrize_indirect(
    {
        "mock_with_course_and_assignment": {
            "course_success": False,
            "assignment_success": False,
        },
    },
    {
        "mock_with_course_and_assignment": {
            "course_success": True,
            "assignment_success": False,
        },
    },
    {
        "mock_with_course_and_assignment": {
            "course_success": False,
            "assignment_success": True,
        },
    },
)
@parametrize(
    {
        "course_arg": ("Course", "F2022"),
        "assignment_arg": "Assignment",
    },
    {
        "course_arg": ("Some Course", "Period"),
        "assignment_arg": "Unknown Assignment",
    },
    {
        "course_arg": ("", ""),
        "assignment_arg": "",
    },
)
def test_course_or_assignment_retrieval_failed(
    track_no_error_logs,
    track_logs,
    mock_with_course_and_assignment,
    course_arg,
    assignment_arg,
):
    track_logs.reset("INFO")
    mapping = ids.get_ids_mapping(course_arg, assignment_arg, log=True)
    # retrievals failed, so nothing should be returned
    assert len(mapping) == 0
    # retrievals failed, so there should be no logs
    assert not track_logs.saw_level_logged("INFO")


@parametrize(
    {"course_obj": MockCourse(1, "Course", "F2022")},
    {"course_obj": MockCourse(2, "Course Name", "Fall 2022")},
)
@parametrize(
    {"assignment_obj": MockAssignment(1, "Assignment", course_id=10)},
    {"assignment_obj": MockAssignment(5, "", course_id=100)},
)
def test_assignment_does_not_belong_to_course(
    track_logs, course_obj, assignment_obj
):
    # check exception
    with pytest.raises(
        ValueError, match=ASSIGNMENT_NOT_BELONG_TO_COURSE_ERROR
    ):
        ids.get_ids_mapping(course_obj, assignment_obj, log=False)
    # check error logs
    track_logs.reset("ERROR")
    mapping = ids.get_ids_mapping(course_obj, assignment_obj, log=True)
    assert len(mapping) == 0
    assert track_logs.saw_msg_logged(
        "ERROR", ASSIGNMENT_NOT_BELONG_TO_COURSE_ERROR
    )


@parametrize(
    {
        "course_obj": MockCourse(1, "Course", "F2022"),
        "assignment_obj": MockAssignment(1, "Assignment", course_id=1),
    },
    {
        "course_obj": MockCourse(2, "", ""),
        "assignment_obj": MockAssignment(2, "", course_id=2),
    },
)
def test_logs_info(
    track_no_error_logs, track_logs, course_obj, assignment_obj
):
    track_logs.reset("INFO")
    ids.get_ids_mapping(course_obj, assignment_obj, log=True)
    assert track_logs.saw_msg_logged(
        "INFO", GETTING_ASSIGNMENT_SUBMISSIONS_INFO, exact=True
    )


@parametrize(
    {"submissions": [], "expected_mapping": {}},
    {
        "submissions": [
            MockSubmission(1, students=["student1", "student2"]),
            MockSubmission(2, students=["student3"]),
            MockSubmission(3, students=["student4"]),
        ],
        "expected_mapping": {
            "student1": 1,
            "student2": 1,
            "student3": 2,
            "student4": 3,
        },
    },
)
def test_creates_mapping_of_submissions(
    track_no_error_logs, submissions, expected_mapping
):
    course_obj, assignment_obj = make_course_assignment_objs(submissions)
    mapping = ids.get_ids_mapping(course_obj, assignment_obj, log=True)
    assert mapping == expected_mapping
    # if not including all the students, none of the values should be
    # None
    assert all(value is not None for value in mapping.values())


@parametrize(
    {
        "students": [
            "student1",
            "student2",
            "student3",
            "student4",
            "student5",
            "test_student",
        ]
    }
)
@parametrize(
    {"submissions": []},
    {
        "submissions": [
            MockSubmission(1, students=["student1", "student2"]),
            MockSubmission(2, students=["student3"]),
            MockSubmission(3, students=["student4"]),
        ],
    },
    {
        "submissions": [
            MockSubmission(3, students=["student3"]),
            MockSubmission(10, students=["test_student"]),
            MockSubmission(20, students=["student4"]),
            MockSubmission(123456, students=["student5"]),
        ],
    },
)
class TestIncludeAllStudents:
    """Tests with the ``include_all_students`` option set.

    In the provided test parameters, there should be some students that
    do not have associated submissions.
    """

    def test_include_all_students_false_course_roster_not_retrieved(
        self,
        track_no_error_logs,
        mock_get_course_roster_not_called,
        students,
        submissions,
    ):
        course_obj, assignment_obj = make_course_assignment_objs(
            submissions=[]
        )
        ids.get_ids_mapping(
            course_obj, assignment_obj, include_all_students=False, log=True
        )
        # the fixture should check that the ``get_course_roster()``
        # function was not called

    @parametrize_indirect(
        {"mock_get_course_roster": {"always_fail": True, "success": False}},
    )
    def test_course_roster_fail(
        self,
        track_no_error_logs,
        track_logs,
        mock_get_course_roster,
        students,
        submissions,
    ):
        """Tests when the course roster retrieval fails.

        Note that this is unlikely to ever happen.
        ``get_course_roster()`` only fails if the course tuple passed to
        it could not fetch an actual codePost course, but within the
        ``get_ids_mapping()`` function, the ``course`` variable is
        guaranteed to be a ``Course`` object.
        """
        mock_get_course_roster.set(students=students)

        track_logs.reset("WARNING")
        course_obj, assignment_obj = make_course_assignment_objs(submissions)
        mapping = ids.get_ids_mapping(
            course_obj, assignment_obj, include_all_students=True, log=True
        )
        # check for the warning message
        assert track_logs.saw_msg_logged(
            "WARNING", COULD_NOT_FETCH_ROSTER_WARNING, exact=True
        )
        # not all the students should be included
        assert any(student not in mapping for student in students)
        assert all(value is not None for value in mapping.values())

    @parametrize_indirect(
        {"mock_get_course_roster": {"success": True}},
    )
    def test_course_roster_success(
        self,
        track_no_error_logs,
        mock_get_course_roster,
        students,
        submissions,
    ):
        mock_get_course_roster.set(students=students)

        course_obj, assignment_obj = make_course_assignment_objs(submissions)
        mapping = ids.get_ids_mapping(
            course_obj, assignment_obj, include_all_students=True, log=True
        )
        # check that all students are included
        assert all(student in mapping for student in students)
        # check that some students do not have a submission
        assert any(value is None for value in mapping.values())


@pytest.mark.usefixtures("track_no_error_logs")
@parametrize(
    # the results in the saved file should be the same, since it does
    # not include students with no submissions
    {"include_all_students": False},
    {"include_all_students": True},
)
class TestSaveFile:
    """Tests with the ``save_file`` option set."""

    @pytest.fixture(autouse=True)
    def fixture_mock_get_course_roster_success(self, mock_get_course_roster):
        # doesn't matter what the students are
        mock_get_course_roster.set(success=True, students=[])
        yield

    def test_save_file_false_file_not_saved(
        self,
        mock_save_csv_not_called,
        include_all_students,
    ):
        course_obj, assignment_obj = make_course_assignment_objs(
            submissions=[]
        )
        ids.get_ids_mapping(
            course_obj,
            assignment_obj,
            include_all_students=include_all_students,
            save_file=False,
            log=True,
        )
        # the fixture should check that the ``save_csv()`` function was
        # not called

    @parametrize_indirect(
        {"mock_get_path": {"success": True, "filepath": "testing.csv"}},
        {"mock_get_path": {"success": True, "filepath": "file.csv"}},
        {"mock_get_path": {"success": True, "filepath": "some_file.csv"}},
    )
    @parametrize_indirect({"mock_save_csv": {"success": True}})
    def test_use_default_file(
        self,
        mock_validate_csv_not_called,
        mock_get_path,
        mock_save_csv,
        include_all_students,
    ):
        course_obj, assignment_obj = make_course_assignment_objs(
            submissions=[]
        )
        ids.get_ids_mapping(
            course_obj,
            assignment_obj,
            include_all_students=include_all_students,
            save_file=True,
            log=True,
        )
        # `validate_csv()` should not be called since the user isn't
        # passing their own file
        assert mock_get_path.times_called > 0
        assert mock_save_csv.times_called > 0
        assert mock_save_csv.file_saved(mock_get_path.get("filepath"))

    @parametrize_indirect({"mock_validate_csv": {"success": False}})
    @parametrize(
        {"filepath": "test.txt"},
        {"filepath": "invalid.png"},
        {"filepath": "not_a_csv"},
    )
    def test_invalid_csv_file(
        self,
        track_logs,
        mock_validate_csv,
        mock_get_path_not_called,
        mock_save_csv_not_called,
        filepath,
        include_all_students,
    ):
        track_logs.reset("WARNING")
        course_obj, assignment_obj = make_course_assignment_objs(
            submissions=[]
        )
        ids.get_ids_mapping(
            course_obj,
            assignment_obj,
            include_all_students=include_all_students,
            save_file=filepath,
            log=True,
        )
        assert mock_validate_csv.times_called > 0
        assert track_logs.saw_msg_logged(
            "WARNING", NOT_SAVING_TO_FILE_WARNING, exact=True
        )
        # `get_path()` and `save_csv()` should not be called since the
        # filepath was not valid

    @parametrize_indirect(
        {
            "mock_validate_csv": {"success": True},
            "mock_get_path": {"success": False},
        }
    )
    @parametrize(
        {"save_file": True},
        {"save_file": "testing.csv"},
        {"save_file": "file.csv"},
    )
    def test_get_path_fails_no_file_saved(
        self,
        mock_validate_csv,
        mock_get_path,
        mock_save_csv_not_called,
        save_file,
        include_all_students,
    ):
        course_obj, assignment_obj = make_course_assignment_objs(
            submissions=[]
        )
        ids.get_ids_mapping(
            course_obj,
            assignment_obj,
            include_all_students=include_all_students,
            save_file=save_file,
            log=True,
        )
        if isinstance(save_file, str):
            assert mock_validate_csv.times_called > 0
        assert mock_get_path.times_called > 0
        # `save_csv()` should not be called since `get_path()` failed

    @parametrize_indirect(
        {
            "mock_validate_csv": {"success": True},
            "mock_get_path": {"success": True},
            "mock_save_csv": {"success": True},
        }
    )
    @parametrize(
        {"filepath": "ids.csv"},
        {"filepath": "testing.csv"},
        {"filepath": "result.csv"},
    )
    def test_valid_csv_file(
        self,
        mock_validate_csv,
        mock_get_path,
        mock_save_csv,
        filepath,
        include_all_students,
    ):
        # make `get_path()` return the filepath being tested
        mock_get_path.set(filepath=filepath)
        course_obj, assignment_obj = make_course_assignment_objs(
            submissions=[]
        )
        ids.get_ids_mapping(
            course_obj,
            assignment_obj,
            include_all_students=include_all_students,
            save_file=filepath,
            log=True,
        )
        assert mock_validate_csv.times_called > 0
        assert mock_get_path.times_called > 0
        assert mock_save_csv.times_called > 0
        assert mock_save_csv.file_saved(filepath)
