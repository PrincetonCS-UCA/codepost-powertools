"""
Tests the file input/output operation functions.
"""

# =============================================================================

import re

import pytest

from codepost_powertools._utils import file_io
from tests.helpers import parametrize, parametrize_indirect
from tests.mocks import MockAssignment, MockCourse

# =============================================================================

# `get_path()` patterns
ASSIGNMENT_NOT_INCLUDED_WARNING = (
    r"Assignment (.+) will not be included: course was not given"
)

# `validate_csv*()` patterns
NOT_CSV_ERROR = r"Not a csv file"

# =============================================================================


class TestGetPath:
    """Tests the function
    :func:`~codepost_powertools._utils.file_io.get_path`.
    """

    def test_not_a_directory_error(self, track_logs, tmp_path):
        start_dir = tmp_path / "start_dir.txt"
        start_dir.touch()
        # check exception
        with pytest.raises(NotADirectoryError):
            file_io.get_path(start_dir=start_dir, log=False)
        # check logging
        track_logs.reset("ERROR")
        success, path = file_io.get_path(start_dir=start_dir, log=True)
        assert not success
        assert path is None
        assert track_logs.saw_level_logged("ERROR")

    @parametrize(
        # single args
        {
            "kwargs": {"filename": "file.txt"},
            "expected_parts": ["file.txt"],
        },
        {
            "kwargs": {"course": MockCourse(name="Course", period="F2022")},
            "expected_parts": ["Course_F2022"],
        },
        {
            "kwargs": {"folder": "folder"},
            "expected_parts": ["folder"],
        },
        # two args
        {
            "kwargs": {
                "filename": "file.txt",
                "course": MockCourse(name="Course", period="F2022"),
            },
            "expected_parts": ["Course_F2022", "file.txt"],
        },
        {
            "kwargs": {
                "filename": "file.txt",
                "folder": "folder",
            },
            "expected_parts": ["folder", "file.txt"],
        },
        {
            "kwargs": {
                "course": MockCourse(name="Course", period="F2022"),
                "assignment": MockAssignment(name="Assignment"),
            },
            "expected_parts": ["Course_F2022", "Assignment"],
        },
        {
            "kwargs": {
                "course": MockCourse(name="Course", period="F2022"),
                "folder": "folder",
            },
            "expected_parts": ["Course_F2022", "folder"],
        },
        # three args
        {
            "kwargs": {
                "filename": "file.txt",
                "course": MockCourse(name="Course", period="F2022"),
                "assignment": MockAssignment(name="Assignment"),
            },
            "expected_parts": ["Course_F2022", "Assignment", "file.txt"],
        },
        {
            "kwargs": {
                "filename": "file.txt",
                "course": MockCourse(name="Course", period="F2022"),
                "folder": "folder",
            },
            "expected_parts": ["Course_F2022", "folder", "file.txt"],
        },
        # four args
        {
            "kwargs": {
                "filename": "file.txt",
                "course": MockCourse(name="Course", period="F2022"),
                "assignment": MockAssignment(name="Assignment"),
                "folder": "folder",
            },
            "expected_parts": [
                "Course_F2022",
                "Assignment",
                "folder",
                "file.txt",
            ],
        },
    )
    def test_parts(
        self, track_no_error_logs, tmp_path, kwargs, expected_parts
    ):
        success, path = file_io.get_path(tmp_path, **kwargs, log=True)
        assert success
        path = path.relative_to(tmp_path)
        assert tuple(path.parts) == tuple(expected_parts)

    @parametrize(
        {
            # include both
            "kwargs": {
                "course": MockCourse(name="Course", period="F2022"),
                "assignment": MockAssignment(name="Assignment"),
            },
            "expected_parts": ["Course_F2022", "Assignment"],
            "has_warning": False,
        },
        {
            # don't include course, so assignment shouldn't be in
            # output
            "kwargs": {"assignment": MockAssignment(name="Assignment")},
            "expected_parts": [],
            "has_warning": True,
        },
        {
            # don't include assignment, which doesn't affect course
            "kwargs": {"course": MockCourse(name="Course", period="F2022")},
            "expected_parts": ["Course_F2022"],
            "has_warning": False,
        },
    )
    def test_course_assignment_parts(
        self,
        track_no_error_logs,
        track_logs,
        tmp_path,
        kwargs,
        expected_parts,
        has_warning,
    ):
        """Tests the special cases of the dependency of ``course`` and
        ``assignment`` on each other.
        """
        track_logs.reset("WARNING")
        success, path = file_io.get_path(tmp_path, **kwargs, log=True)
        assert success
        path = path.relative_to(tmp_path)
        assert tuple(path.parts) == tuple(expected_parts)
        if has_warning:
            assert track_logs.saw_msg_logged(
                "WARNING",
                ASSIGNMENT_NOT_INCLUDED_WARNING,
            )


class TestValidateCsv:
    """Tests the functions
    :func:`~codepost_powertools._utils.file_io.validate_csv_silent` and
    :func:`~codepost_powertools._utils.file_io.validate_csv`.
    """

    @parametrize_indirect(
        {"tmp_file": "file.txt"},
        {"tmp_file": "file.csv.txt"},
        {"tmp_file": "file"},
    )
    class TestError:
        """Tests function calls that are expected to have an error."""

        def test_silent(self, tmp_file):
            success, error_msg = file_io.validate_csv_silent(tmp_file)
            assert not success
            assert error_msg is not None
            match = re.search(NOT_CSV_ERROR, error_msg)
            assert match is not None

        def test_validate(self, track_logs, tmp_file):
            # check exception
            with pytest.raises(ValueError, match=NOT_CSV_ERROR):
                file_io.validate_csv(tmp_file, log=False)
            # check logs
            track_logs.reset("ERROR")
            success = file_io.validate_csv(tmp_file, log=True)
            assert not success
            assert track_logs.saw_msg_logged("ERROR", NOT_CSV_ERROR)

    @parametrize_indirect(
        {"tmp_file": "file.csv"},
        {"tmp_file": "file.txt.csv"},
    )
    class TestNoError:
        """Tests function calls that are expected to have no error."""

        def test_silent(self, tmp_file):
            success, error_msg = file_io.validate_csv_silent(tmp_file)
            assert success
            assert error_msg is None

        def test_validate(self, track_no_error_logs, tmp_file):
            success = file_io.validate_csv(tmp_file, log=True)
            assert success


class TestSaveCsv:
    """Tests the function
    :func:`~codepost_powertools._utils.file_io.save_csv`.

    We will assume that the ``comma`` package properly handles invalid
    data, so only valid data will be tested.
    """

    DATA = [{"col1": "val1", "col2": 0}, {"col1": "val2", "col2": 1}]
    DATA_STR = "\n".join(["col1,col2", "val1,0", "val2,1", ""])

    @parametrize_indirect(
        {"tmp_file": "file.txt"},
        {"tmp_file": "file"},
    )
    def test_error(self, track_logs, tmp_file):
        # The only error that occurs in `save_csv()` is validating that
        # the file has a ".csv" extension
        # check exception
        with pytest.raises(ValueError, match=NOT_CSV_ERROR):
            file_io.save_csv(self.DATA, tmp_file, log=False)
        assert not tmp_file.exists()
        # check error log
        track_logs.reset("ERROR")
        success = file_io.save_csv(self.DATA, tmp_file, log=True)
        assert not success
        assert not tmp_file.exists()
        assert track_logs.saw_msg_logged("ERROR", NOT_CSV_ERROR)

    @parametrize(
        {
            "tmp_file": "file.csv",
            "description": "data",
        },
        {
            "tmp_file": "file.csv",
            "description": "information",
        },
        {
            "tmp_file": (["path", "to", "file.csv"], None),
            "description": "some stuff",
        },
        indirect=["tmp_file"],
    )
    def test_no_error(
        self, track_no_error_logs, track_logs, tmp_file, description
    ):
        track_logs.reset("INFO")
        success = file_io.save_csv(self.DATA, tmp_file, log=True)
        assert success
        assert tmp_file.exists()
        assert tmp_file.read_text(encoding="utf-8") == self.DATA_STR
        # check log messages
        track_logs.saw_msg_logged("INFO", rf"Saving {description} to")
