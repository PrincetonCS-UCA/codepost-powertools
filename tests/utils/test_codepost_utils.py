"""
Tests the codePost utilities.

The tests in this file are defined in the following order:
- course_str()
- get_course()
- @with_course
- get_course_roster()
- get_assignment()
- @with_course_and_assignment

Dependency functions will be mocked.

Any functions decorated with ``@with_course`` or
``@with_course_and_assignment`` cannot be separated from their
decorators (which are applied when the file is loaded), so we must mock
``get_course()`` and ``get_assignment()`` instead.
"""

# =============================================================================

import pytest

from codepost_powertools.utils import codepost_utils as cp_utils
from tests.helpers import parametrize, parametrize_indirect
from tests.mocks import MockAssignment, MockCourse

# =============================================================================

# `get_course()` patterns
COURSE_NOT_FOUND_ERROR = r"No course found with name .+ and period .+"
MULTIPLE_COURSES_FOUND_WARNING = (
    r"Multiple courses found with name .+ and period .+"
)

# `get_assignment()` patterns
GETTING_ASSIGNMENT_INFO = r"Getting assignment"
ASSIGNMENT_NOT_FOUND_ERROR = r"Assignment .+ not found"

# =============================================================================


@pytest.fixture(scope="module", autouse=True)
def fixture_fix_decorators(module_codepost_patch_types):
    """This fixture patches the codePost types so that the decorators
    ``@with_course`` and ``@with_course_and_assignment`` work properly
    with the mock objects.
    """
    yield


# =============================================================================


def assert_course(
    course, *, id_=None, name=None, period=None, course_tuple=None
):
    assert course is not None
    if id_ is not None:
        assert course.id == id_
    if name is None and course_tuple is not None:
        name = course_tuple[0]
    if name is not None:
        assert course.name == name
    if period is None and course_tuple is not None:
        period = course_tuple[1]
    if period is not None:
        assert course.period == period


def assert_assignment(assignment, *, id_=None, name=None):
    assert assignment is not None
    if id_ is not None:
        assert assignment.id == id_
    if name is not None:
        assert assignment.name == name


# =============================================================================


class TestCourseStr:
    """Tests the function
    :func:`~codepost_powertools.utils.codepost_utils.course_str`.
    """

    @parametrize(
        {
            "course": MockCourse(name="Course", period="F2022"),
            "delim": " ",
            "expected_str": "Course F2022",
        },
        {
            "course": MockCourse(name="Course", period="F2022"),
            "delim": "_",
            "expected_str": "Course_F2022",
        },
        {
            "course": MockCourse(name="Course Name", period="Fall 2022"),
            "delim": "-",
            "expected_str": "Course Name-Fall 2022",
        },
        {
            "course": MockCourse(name="", period=""),
            "delim": " ",
            "expected_str": " ",
        },
        {
            "course": MockCourse(name="Course", period=""),
            "delim": " ",
            "expected_str": "Course ",
        },
        {
            "course": MockCourse(name="Course", period="F2022"),
            "delim": "",
            "expected_str": "CourseF2022",
        },
        {
            "course": MockCourse(name="Course", period="F2022"),
            "delim": "delim",
            "expected_str": "CoursedelimF2022",
        },
    )
    def test(self, course, delim, expected_str):
        result = cp_utils.course_str(course, delim=delim)
        assert result == expected_str


class TestGetCourse:
    """Tests the function
    :func:`~codepost_powertools.utils.codepost_utils.get_course`.
    """

    @pytest.fixture(scope="class", autouse=True)
    def fixture_inject_codepost_courses(self, class_codepost_patch_courses):
        """Injects mock codePost courses."""
        MOCK_COURSES = [
            MockCourse(
                1,
                "Course",
                "F2022",
                assignments=[
                    MockAssignment(1, "Assignment1"),
                    MockAssignment(2, "Assignment2"),
                ],
            ),
            # courses 2 and 3 have the same name and period
            MockCourse(
                2,
                "Course",
                "F2023",
                assignments=[
                    MockAssignment(1, "Assignment1"),
                    MockAssignment(2, "Assignment2"),
                    MockAssignment(5, "Assignment3"),
                ],
            ),
            MockCourse(
                3,
                "Course",
                "F2023",
                assignments=[
                    MockAssignment(3, "Assignment1"),
                    MockAssignment(4, "Assignment2"),
                ],
            ),
            MockCourse(
                4,
                "Course",
                "F2024",
                assignments=[
                    MockAssignment(10, "Assignment1"),
                    MockAssignment(20, "Assignment2"),
                ],
            ),
        ]
        class_codepost_patch_courses.extend(MOCK_COURSES)
        yield class_codepost_patch_courses
        class_codepost_patch_courses = class_codepost_patch_courses[
            : -len(MOCK_COURSES)
        ]

    @parametrize(
        {
            "course_name": "Course",
            "course_period": "F2021",
        },
        {
            "course_name": "Course Name",
            "course_period": "F2022",
        },
        {
            "course_name": "Unknown Course",
            "course_period": "1746",
        },
        {
            "course_name": "",
            "course_period": "",
        },
        {
            "course_name": "Course",
            "course_period": "",
        },
        {
            "course_name": "",
            "course_period": "F2022",
        },
    )
    def test_error(self, track_logs, course_name, course_period):
        # check exception
        with pytest.raises(ValueError, match=COURSE_NOT_FOUND_ERROR):
            cp_utils.get_course(course_name, course_period, log=False)
        # check error logs
        track_logs.reset("ERROR")
        success, course = cp_utils.get_course(
            course_name, course_period, log=True
        )
        assert not success
        assert course is None
        track_logs.saw_msg_logged("ERROR", COURSE_NOT_FOUND_ERROR)

    @parametrize(
        {"course_name": "Course", "course_period": "F2022", "expected_id": 1},
        {"course_name": "Course", "course_period": "F2023", "expected_id": 2},
        {"course_name": "Course", "course_period": "F2024", "expected_id": 4},
    )
    def test_no_error(
        self, track_no_error_logs, course_name, course_period, expected_id
    ):
        success, course = cp_utils.get_course(
            course_name, course_period, log=True
        )
        assert success
        assert_course(
            course, id_=expected_id, name=course_name, period=course_period
        )

    @parametrize(
        {"course_name": "Course", "course_period": "F2023", "expected_id": 2},
    )
    def test_multiple_courses_found(
        self,
        track_no_error_logs,
        track_logs,
        course_name,
        course_period,
        expected_id,
    ):
        track_logs.reset("WARNING")
        success, course = cp_utils.get_course(
            course_name, course_period, log=True
        )
        assert success
        assert_course(
            course, id_=expected_id, name=course_name, period=course_period
        )
        assert track_logs.saw_msg_logged(
            "WARNING", MULTIPLE_COURSES_FOUND_WARNING
        )


class TestWithCourse:
    """Tests the decorator.
    :deco:`~codepost_powertools.utils.codepost_utils.with_course`.
    """

    @pytest.fixture(name="test_func", scope="class")
    def fixture_get_test_func(self):
        """Returns a function that is decorated by ``@with_course`` and
        returns the course that is passed to it.
        """
        yield cp_utils.with_course(lambda course, *args, **kwargs: course)

    @parametrize(
        {"course_tuple": ("Course", "F2022")},
        {"course_tuple": ("Course Name", "Fall 2022")},
        {"course_tuple": ("Unknown Course", "1746")},
        {"course_tuple": ("", "")},
        {"course_tuple": ("Course", "")},
        {"course_tuple": ("", "F2022")},
    )
    class TestCourseTuple:
        """Tests with course tuples."""

        def test_dne(self, mock_get_course_fail, test_func, course_tuple):
            course = test_func(course_tuple)
            assert course is None
            assert mock_get_course_fail.times_called > 0

        def test_exists(
            self, mock_get_course_success, test_func, course_tuple
        ):
            course = test_func(course_tuple)
            assert_course(course, course_tuple=course_tuple)
            assert mock_get_course_success.times_called > 0

    @parametrize(
        {"course_obj": MockCourse(name="Course", period="F2022")},
        {"course_obj": MockCourse(name="Course Name", period="Fall 2022")},
        {"course_obj": MockCourse(name="", period="")},
    )
    def test_course_obj(
        self, mock_get_course_not_called, test_func, course_obj
    ):
        course = test_func(course_obj)
        assert course is course_obj


@pytest.mark.usefixtures("codepost_patch_rosters")
class TestGetCourseRoster:
    """Tests the function
    :func:`~codepost_powertools.utils.codepost_utils.get_course_roster`.

    In these tests, we assume that the roster retrieval does not fail,
    given that the course exists.
    """

    @parametrize(
        {"course_tuple": ("Course", "F2022")},
        {"course_tuple": ("Course Name", "Fall 2022")},
        {"course_tuple": ("Unknown Course", "1746")},
        {"course_tuple": ("", "")},
        {"course_tuple": ("Course", "")},
        {"course_tuple": ("", "F2022")},
    )
    class TestCourseTuple:
        """Tests with course tuples."""

        def test_dne(self, mock_get_course_fail, course_tuple):
            success, roster = cp_utils.get_course_roster(course_tuple)
            assert not success
            assert roster is None
            assert mock_get_course_fail.times_called > 0

        def test_exists(self, mock_get_course_success, course_tuple):
            success, roster = cp_utils.get_course_roster(course_tuple)
            assert success
            assert roster is not None
            assert mock_get_course_success.times_called > 0

    @parametrize(
        {"course_obj": MockCourse(1, "Course", "F2022")},
        {"course_obj": MockCourse(2, "Course Name", "Fall 2022")},
        {"course_obj": MockCourse(10, "", "")},
    )
    def test_course_obj(self, mock_get_course_not_called, course_obj):
        success, roster = cp_utils.get_course_roster(course_obj)
        assert success
        assert roster is not None
        assert roster.id == course_obj.id


class TestGetAssignment:
    """Tests the function
    :func:`~codepost_powertools.utils.codepost_utils.get_assignment`.
    """

    @parametrize(
        {"course_tuple": ("Course", "F2022")},
        {"course_tuple": ("Course Name", "Fall 2022")},
        {"course_tuple": ("", "")},
    )
    @parametrize(
        {"assignment_name": "Assignment1"},
        {"assignment_name": "Assignment2"},
    )
    def test_course_tuple_dne(
        self,
        track_no_error_logs,
        track_logs,
        mock_get_course_fail,
        course_tuple,
        assignment_name,
    ):
        # since the course could not be fetched, the assignment isn't
        # even attempted. therefore, we shouldn't get any logs
        track_logs.reset("INFO")
        success, assignment = cp_utils.get_assignment(
            course_tuple, assignment_name, log=True
        )
        assert not success
        assert assignment is None
        assert mock_get_course_fail.times_called > 0
        assert not track_logs.saw_msg_logged("INFO", GETTING_ASSIGNMENT_INFO)

    @parametrize_indirect(
        {
            "mock_get_course": {
                "success": True,
                "assignments": [
                    MockAssignment(1, "Assignment1"),
                    MockAssignment(2, "Assignment2"),
                    MockAssignment(3, "Assignment3"),
                ],
            },
        },
    )
    @parametrize(
        {"course_tuple": ("Course", "F2022")},
        {"course_tuple": ("Course Name", "Fall 2022")},
    )
    class TestCourseTupleExists:
        """Tests with an existing course tuple."""

        @pytest.fixture(autouse=True)
        def fixture_course_tuple_exists(self, mock_get_course):
            """Uses the mock ``get_course()`` that always succeeds, and
            checks that it was called during the test.
            """
            yield mock_get_course
            assert mock_get_course.times_called > 0

        @parametrize(
            {"assignment_name": "Assignment Name"},
            {"assignment_name": "Unknown Assignment"},
            {"assignment_name": ""},
        )
        def test_assignment_dne(
            self,
            track_logs,
            course_tuple,
            assignment_name,
        ):
            # check exception
            with pytest.raises(ValueError, match=ASSIGNMENT_NOT_FOUND_ERROR):
                cp_utils.get_assignment(
                    course_tuple, assignment_name, log=False
                )
            # check error logs
            track_logs.reset("ERROR")
            success, assignment = cp_utils.get_assignment(
                course_tuple, assignment_name, log=True
            )
            assert not success
            assert assignment is None
            assert track_logs.saw_msg_logged(
                "ERROR", ASSIGNMENT_NOT_FOUND_ERROR
            )

        @parametrize(
            {"assignment_name": "Assignment1", "expected_id": 1},
            {"assignment_name": "Assignment2", "expected_id": 2},
            {"assignment_name": "Assignment3", "expected_id": 3},
        )
        def test_assignment_exists(
            self,
            track_no_error_logs,
            course_tuple,
            assignment_name,
            expected_id,
        ):
            success, assignment = cp_utils.get_assignment(
                course_tuple, assignment_name, log=True
            )
            assert success
            assert_assignment(
                assignment, id_=expected_id, name=assignment_name
            )

    @parametrize(
        {
            "course_obj": MockCourse(
                1,
                "Course",
                "F2022",
                assignments=[
                    MockAssignment(1, "Assignment1"),
                    MockAssignment(2, "Assignment2"),
                    MockAssignment(3, "Assignment3"),
                ],
            )
        },
    )
    class TestCourseObj:
        """Tests with a course object."""

        @parametrize(
            {"assignment_name": "Assignment5"},
            {"assignment_name": "Unknown Assignment"},
        )
        def test_assignment_dne(
            self,
            track_logs,
            mock_get_course_not_called,
            course_obj,
            assignment_name,
        ):
            # check exception
            with pytest.raises(ValueError, match=ASSIGNMENT_NOT_FOUND_ERROR):
                cp_utils.get_assignment(course_obj, assignment_name, log=False)
            # check error logs
            track_logs.reset("ERROR")
            success, assignment = cp_utils.get_assignment(
                course_obj, assignment_name, log=True
            )
            assert not success
            assert assignment is None
            assert track_logs.saw_msg_logged(
                "ERROR", ASSIGNMENT_NOT_FOUND_ERROR
            )

        @parametrize(
            {"assignment_name": "Assignment1", "expected_id": 1},
            {"assignment_name": "Assignment2", "expected_id": 2},
            {"assignment_name": "Assignment3", "expected_id": 3},
        )
        def test_assignment_exists(
            self,
            track_no_error_logs,
            mock_get_course_not_called,
            course_obj,
            assignment_name,
            expected_id,
        ):
            success, assignment = cp_utils.get_assignment(
                course_obj, assignment_name, log=True
            )
            assert success
            assert_assignment(
                assignment, id_=expected_id, name=assignment_name
            )


class TestWithCourseAndAssignment:
    # pylint: disable=line-too-long
    """Tests the decorator
    :deco:`~codepost_powertools.utils.codepost_utils.with_course_and_assignment`.
    """
    # pylint: enable=line-too-long

    @pytest.fixture(name="test_func", scope="class")
    def fixture_get_test_func(self):
        """Returns a function that is decorated by
        ``@with_course_and_assignment`` and returns the course and
        assignment that are passed to it.
        """
        yield cp_utils.with_course_and_assignment(
            lambda course, assignment, *args, **kwargs: (course, assignment)
        )

    @parametrize(
        {
            "course_tuple": ("Course", "F2022"),
            "assignment_arg": "Assignment",
        },
        {
            "course_tuple": ("Unknown Course", "Fall 2022"),
            "assignment_arg": "Assignment",
        },
        {
            "course_tuple": ("", ""),
            "assignment_arg": MockAssignment(),
        },
        {
            "course_tuple": ("Bad Course", "010"),
            "assignment_arg": MockAssignment(),
        },
    )
    def test_course_tuple_dne(
        self,
        mock_get_course_fail,
        mock_get_assignment_not_called,
        test_func,
        course_tuple,
        assignment_arg,
    ):
        result_course, result_assignment = test_func(
            course_tuple, assignment_arg
        )
        assert result_course is None
        assert result_assignment is None
        assert mock_get_course_fail.times_called > 0

    @parametrize(
        {"course_tuple": ("Course", "F2022")},
        {"course_tuple": ("Course Name", "Fall 2022")},
        {"course_tuple": ("", "")},
    )
    class TestCourseTupleExists:
        """Tests with an existing course tuple."""

        @pytest.fixture(autouse=True)
        def fixture_course_tuple_exists(self, mock_get_course_success):
            """Uses the mock ``get_course()`` that always succeeds, and
            checks that it was called during the test.
            """
            yield mock_get_course_success
            assert mock_get_course_success.times_called > 0

        @parametrize(
            {"assignment_name": "Assignment"},
            {"assignment_name": "Unknown Assignment"},
            {"assignment_name": "Some Assignment"},
        )
        class TestAssignmentName:
            """Tests using an assignment name argument."""

            def test_dne(
                self,
                mock_get_assignment_fail,
                test_func,
                course_tuple,
                assignment_name,
            ):
                result_course, result_assignment = test_func(
                    course_tuple, assignment_name
                )
                assert result_course is None
                assert result_assignment is None
                assert mock_get_assignment_fail.times_called > 0

            def test_exists(
                self,
                mock_get_assignment_success,
                test_func,
                course_tuple,
                assignment_name,
            ):
                result_course, result_assignment = test_func(
                    course_tuple, assignment_name
                )
                assert_course(result_course, course_tuple=course_tuple)
                assert_assignment(result_assignment, name=assignment_name)
                assert mock_get_assignment_success.times_called > 0

        @parametrize(
            {"assignment_obj": MockAssignment(1, "Assignment")},
            {"assignment_obj": MockAssignment(2, "Assignment Name")},
            {"assignment_obj": MockAssignment(10, "")},
            {"assignment_obj": MockAssignment()},
        )
        def test_assignment_obj_exists(
            self,
            mock_get_assignment_not_called,
            test_func,
            course_tuple,
            assignment_obj,
        ):
            result_course, result_assignment = test_func(
                course_tuple, assignment_obj
            )
            assert_course(result_course, course_tuple=course_tuple)
            assert result_assignment is assignment_obj

    @parametrize(
        {"course_obj": MockCourse(1, "Course", "F2022")},
        {"course_obj": MockCourse(2, "Course Name", "Fall 2022")},
    )
    class TestCourseObj:
        """Tests with a course object."""

        @pytest.fixture(autouse=True)
        def fixture_use_course_obj(self, mock_get_course_not_called):
            """Ensures that the ``get_course()`` mock was not called
            during any test.
            """
            yield mock_get_course_not_called

        @parametrize(
            {"assignment_name": "Assignment"},
            {"assignment_name": "Unknown Assignment"},
            {"assignment_name": "Some Assignment"},
            {"assignment_name": ""},
        )
        class TestAssignmentName:
            """Tests using an assignment name argument."""

            def test_dne(
                self,
                mock_get_assignment_fail,
                test_func,
                course_obj,
                assignment_name,
            ):
                result_course, result_assignment = test_func(
                    course_obj, assignment_name
                )
                assert result_course is None
                assert result_assignment is None
                assert mock_get_assignment_fail.times_called > 0

            def test_exists(
                self,
                mock_get_assignment_success,
                test_func,
                course_obj,
                assignment_name,
            ):
                result_course, result_assignment = test_func(
                    course_obj, assignment_name
                )
                assert result_course is course_obj
                assert_assignment(result_assignment, name=assignment_name)
                assert mock_get_assignment_success.times_called > 0

        @parametrize(
            {"assignment_obj": MockAssignment(1, "Assignment")},
            {"assignment_obj": MockAssignment(2, "Assignment Name")},
            {"assignment_obj": MockAssignment(10, "")},
            {"assignment_obj": MockAssignment()},
        )
        def test_assignment_obj_exists(
            self,
            mock_get_assignment_not_called,
            test_func,
            course_obj,
            assignment_obj,
        ):
            result_course, result_assignment = test_func(
                course_obj, assignment_obj
            )
            assert result_course is course_obj
            assert result_assignment is assignment_obj
