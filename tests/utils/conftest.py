"""
Fixtures for the ``utils`` utilities.

These fixtures are available for use in tests outside of this
subpackage. However, due to the way ``pytest`` works, any other test
files that want to use the fixtures in this file must import all the
dependencies of those fixtures as well, so that they're defined in the
scope of the calling file.

Fixtures defined:
- mock_get_course
  - mock_get_course_fail
  - mock_get_course_success
  - mock_get_course_not_called
- mock_with_course
- mock_get_course_roster
- mock_get_assignment
  - mock_get_assignment_fail
  - mock_get_assignment_success
  - mock_get_assignment_not_called
- mock_with_course_and_assignment
"""

# =============================================================================

import pytest

from codepost_powertools.utils import codepost_utils
from tests.helpers import (
    MockFunction,
    get_request_param,
    patch_with_default_module,
)
from tests.mocks import MockAssignment, MockCourse, MockRoster

patch_mock_func = patch_with_default_module(codepost_utils)

# =============================================================================


class MockGetCourse(MockFunction):
    """A mock for the ``get_course()`` function."""

    def __init__(self, success=False, assignments=None):
        super().__init__(enable_set=True)
        self._success = success
        self._assignments = assignments or []

    def mock(self, name, period, log=False):
        if not self._success:
            # mock a failure
            return False, None
        # mock a success with the given name and period
        return True, MockCourse(
            id_=self._times_called,
            name=name,
            period=period,
            assignments=self._assignments,
        )


@pytest.fixture(name="mock_get_course")
def fixture_mock_get_course(request):
    """Creates a mock for the ``get_course()`` function.

    Accepts the following kwargs:
        success (bool): Whether the course retrieval is successful.
        assignment (List[MockAssignment]): The assignments that
            retrieved courses should have.
    """
    kwargs = get_request_param(request, default={})
    mock_func = MockGetCourse(**kwargs)
    with pytest.MonkeyPatch.context() as monkeypatch:
        patch_mock_func(monkeypatch, request, "get_course", mock_func)
        yield mock_func


@pytest.fixture(name="mock_get_course_fail")
def fixture_mock_get_course_fail(mock_get_course):
    """A convenience fixture for mocking the ``get_course()`` function
    to always fail.
    """
    mock_get_course.set(success=False)
    yield mock_get_course


@pytest.fixture(name="mock_get_course_success")
def fixture_mock_get_course_success(mock_get_course):
    """A convenience fixture for mocking the ``get_course()`` function
    to always succeed.
    """
    mock_get_course.set(success=True)
    yield mock_get_course


@pytest.fixture(name="mock_get_course_not_called")
def fixture_mock_get_course_not_called(mock_get_course):
    """A convenience fixture for mocking the ``get_course()`` function
    to always fail, then checking that it was never called.
    """
    mock_get_course.set(success=False)
    yield mock_get_course
    assert mock_get_course.times_called == 0


# =============================================================================


@pytest.fixture(name="mock_with_course")
def fixture_mock_with_course(request, codepost_patch_types, mock_get_course):
    """Mocks the ``@with_course`` decorator.

    Accepts the following kwargs:
        success (bool): Whether the course retrieval is successful.
        assignments (List[MockAssignment]): The assignments that
            retrieved courses should have.

    .. note::
       The decorator itself can't be mocked, but the behavior when using
       this decorator will essentially be the same as actually mocking
       the decorator and all the functions it decorated.
    """
    kwargs = get_request_param(request, default={})
    mock_get_course.set(**kwargs)
    yield


# =============================================================================


class MockGetCourseRoster(MockFunction):
    """A mock for the ``get_course_roster()`` function."""

    def __init__(self, always_fail=False, success=False, students=None):
        super().__init__(enable_set=True)
        self._always_fail = always_fail
        self._success = success
        self._students = students or []

    def mock(self, course_arg, log=False):
        if self._always_fail:
            # mock a failure always
            return False, None
        if isinstance(course_arg, MockCourse):
            id_ = course_arg.id
        else:
            if not self._success:
                # failed to retrieve the course; mock a failure
                return False, None
            id_ = None
        # mock a success with the given name and period
        return True, MockRoster(id_=id_, students=self._students)


@pytest.fixture(name="mock_get_course_roster")
def fixture_mock_get_course_roster(request, mock_with_course):
    """Mocks the ``get_course_roster()`` function.

    If a given course arg has an "id" attribute, the retrieved roster
    will have that id. Otherwise, the id will be undefined.

    Accepts the following kwargs:
        always_fail (bool): Whether to always fail the function call,
            regardless of whether the input is already a Course object.
        success (bool): Whether the course retrieval is successful.
        students (Sequence[str]): The students that retrieved rosters
            should have.
    """
    kwargs = get_request_param(request, default={})
    mock_func = MockGetCourseRoster(**kwargs)
    with pytest.MonkeyPatch.context() as monkeypatch:
        patch_mock_func(monkeypatch, request, "get_course_roster", mock_func)
        yield mock_func


@pytest.fixture(name="mock_get_course_roster_not_called")
def fixture_mock_get_course_roster_not_called(mock_get_course_roster):
    """A convenience fixture for mocking the ``get_course_roster()``
    function to always fail, then checking that it was never called.
    """
    mock_get_course_roster.set(always_fail=True)
    yield mock_get_course_roster
    assert mock_get_course_roster.times_called == 0


# =============================================================================


class MockGetAssignment(MockFunction):
    """A mock for the ``get_assignment()`` function."""

    def __init__(self, success=False):
        super().__init__(enable_set=True)
        self._success = success

    def mock(self, course, assignment_name, log=False):
        if not self._success:
            # mock a failure
            return False, None
        # mock a success with the given name
        return True, MockAssignment(
            id_=self._times_called, name=assignment_name
        )


@pytest.fixture(name="mock_get_assignment")
def fixture_mock_get_assignment(request):
    """Creates a mock for the ``get_assignment()`` function.

    Accepts the following kwargs:
        success (bool): Whether the assignment retrieval is successful.
    """
    kwargs = get_request_param(request, default={})
    mock_func = MockGetAssignment(**kwargs)
    with pytest.MonkeyPatch.context() as monkeypatch:
        patch_mock_func(monkeypatch, request, "get_assignment", mock_func)
        yield mock_func


@pytest.fixture(name="mock_get_assignment_fail")
def fixture_mock_get_assignment_fail(mock_get_assignment):
    """A convenience fixture for mocking the ``get_assignment()``
    function to always fail.
    """
    mock_get_assignment.set(success=False)
    yield mock_get_assignment


@pytest.fixture(name="mock_get_assignment_success")
def fixture_mock_get_assignment_success(mock_get_assignment):
    """A convenience fixture for mocking the ``get_assignment()``
    function to always succeed.
    """
    mock_get_assignment.set(success=True)
    yield mock_get_assignment


@pytest.fixture(name="mock_get_assignment_not_called")
def fixture_mock_get_assignment_not_called(mock_get_assignment_fail):
    """A convenience fixture for mocking the ``get_assignment()``
    function to always fail, then checking that it was never called.
    """
    yield mock_get_assignment_fail
    assert mock_get_assignment_fail.times_called == 0


# =============================================================================


@pytest.fixture(name="mock_with_course_and_assignment")
def fixture_mock_with_course_and_assignment(
    request, codepost_patch_types, mock_get_course, mock_get_assignment
):
    """Mocks the ``@with_course_and_assignment`` decorator.

    Accepts the following kwargs:
        course_success (bool): Whether the course retrieval is
            successful.
        assignment_success (bool): Whether the assignment retrieval is
            successful.
        assignments (Sequence[MockAssignment]): The assignments that
            retrieved courses should have.

    .. note::
       The decorator itself can't be mocked, but the behavior when using
       this decorator will essentially be the same as actually mocking
       the decorator and all the functions it decorated.
    """
    kwargs = get_request_param(request, default={})
    get_course_kwargs = {}
    for request_key, kwargs_key in (
        ("course_success", "success"),
        ("assignments", "assignments"),
    ):
        if request_key in kwargs:
            get_course_kwargs[kwargs_key] = kwargs[request_key]
    mock_get_course.set(**get_course_kwargs)
    get_assignment_kwargs = {}
    for request_key, kwargs_key in (("assignment_success", "success"),):
        if request_key in kwargs:
            get_assignment_kwargs[kwargs_key] = kwargs[request_key]
    mock_get_assignment.set(**get_assignment_kwargs)
    yield
