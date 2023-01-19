"""
Global shared fixtures for testing.
"""

# =============================================================================

from typing import Sequence

import codepost
import pytest

from codepost_powertools.utils import cptypes
from tests.helpers import get_request_param, multi_scope_fixture
from tests.mocks import MockAssignment, MockCourse, MockLogger, MockRoster

# =============================================================================


@pytest.fixture(name="tmp_file")
def fixture_create_tmp_file(request, tmp_path):
    """Creates a temporary file.

    Accepts either:
    - The file name. It will not be created.
    - A tuple of the file name and the contents of the file.
      - The file name can optionally be a sequence denoting the path to
        the file.
      - If the contents are None, the file will not be created.
    """
    args = get_request_param(request)
    if isinstance(args, str):
        filename = [args]
        contents = None
    elif isinstance(args, Sequence):
        if len(args) != 2:
            raise ValueError(
                "given sequence does not have length 2 (filename and contents)"
            )
        filename, contents = args
        if isinstance(filename, str):
            filename = [filename]
    else:
        raise TypeError(f"unknown type for `args`: {args.__class__.__name__}")
    path = tmp_path.joinpath(*filename)
    if contents is not None:
        path.write_text(contents, encoding="utf-8")
    else:
        path.unlink(missing_ok=True)
    yield path


# =============================================================================


@pytest.fixture(name="track_logs")
def fixture_track_logs():
    """Returns a :class:`~tests.mocks.MockLogger` object that tracks
    logs made to all levels.
    """
    with pytest.MonkeyPatch.context() as monkeypatch:
        yield MockLogger(monkeypatch)


@pytest.fixture(name="track_no_error_logs")
def fixture_track_no_error_logs(track_logs):
    """After the test has run, makes sure that no errors were logged."""
    yield track_logs
    assert not track_logs.saw_level_logged("ERROR"), "errors were logged"


# =============================================================================


@multi_scope_fixture(
    name="codepost_patch_courses",
    scopes=["function", "class"],
    default_scope="function",
)
def fixture_codepost_patch_courses(request):
    """Patch the ``codepost`` package with custom courses and
    assignments. Returns the list of courses, which can be modified
    in-place.
    """
    courses = get_request_param(request, default=[])

    with pytest.MonkeyPatch.context() as monkeypatch:
        # retrieving the courses from codePost will return this list
        monkeypatch.setattr(
            codepost.course,
            "iter_available",
            lambda *args, **kwargs: iter(courses),
        )

        yield courses


@pytest.fixture(name="codepost_patch_rosters")
def fixture_codepost_patch_rosters():
    """Mocks the codePost ``roster.retrieve`` function to return a
    :class:`~tests.mocks.MockRoster` object.
    """

    rosters = {}

    with pytest.MonkeyPatch.context() as monkeypatch:
        # retrieving a roster will return a MockRoster associated with the
        # request course id
        monkeypatch.setattr(
            codepost.roster,
            "retrieve",
            lambda id_: rosters.setdefault(id_, MockRoster(id_)),
        )

        yield


@multi_scope_fixture(
    name="codepost_patch_types",
    scopes=["function", "module"],
    default_scope="function",
)
def fixture_codepost_patch_types():
    """Patches ``cptypes`` so that the
    :func:`~codepost_powertools.utils.cptypes.isinstance_cp()` function
    will work with mocked classes.
    """

    replaced_types = {}
    for old_type, mock in (
        (cptypes.Course, MockCourse),
        (cptypes.Roster, MockRoster),
        (cptypes.Assignment, MockAssignment),
    ):
        # pylint: disable=protected-access
        # monkeypatch doesn't work here because it expects `name` to be
        # a string, but the keys of this dict are `NewType`s
        replaced_types[old_type] = cptypes._CP_TYPES[old_type]
        cptypes._CP_TYPES[old_type] = mock

    yield

    # restore the types
    for old_type, old_value in replaced_types.items():
        # pylint: disable=protected-access
        cptypes._CP_TYPES[old_type] = old_value
