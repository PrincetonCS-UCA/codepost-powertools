"""
Mock classes for testing.
"""

# =============================================================================

import itertools
import re
from collections import defaultdict

import google.auth.exceptions
import gspread
from gspread.utils import (
    ValueRenderOption,
    a1_range_to_grid_range,
    a1_to_rowcol,
)
from loguru._logger import Logger

# =============================================================================


class MockLogger:
    """A mock logger that keeps track of the log calls to each level."""

    def __init__(self, monkeypatch):
        self._logs = None
        self.reset()
        monkeypatch.setattr(Logger, "_log", self._logged_error_hook)

    def _logged_error_hook(self, level, *log_args):
        # assume the last 3 are these args
        *_, message, args, kwargs = log_args
        self._logs[level].append(message.format(*args, **kwargs))

    def reset(self, *levels):
        if len(levels) > 0:
            # pop these levels
            for level in levels:
                self._logs.pop(level, None)
        else:
            # reset everything
            self._logs = defaultdict(list)

    def saw_level_logged(self, level):
        return self.num_level_logged(level) > 0

    def num_level_logged(self, level):
        return len(self._logs[level])

    def saw_msg_logged(self, level, pattern, exact=False):
        level_logs = self._logs[level]
        if len(level_logs) == 0:
            print(f"No logs for level {level}")
            return False
        for msg in level_logs:
            if exact:
                if msg == pattern:
                    return True
            else:
                match = re.search(pattern, msg)
                if match is not None:
                    return True
        print(f"Logs for level {level}:", *level_logs, sep="\n  ")
        return False


# =============================================================================


class MockCourse:
    """A mock of a codePost course."""

    def __init__(self, id_=None, name=None, period=None, *, assignments=None):
        self.id = id_
        self.name = name
        self.period = period
        self.assignments = assignments or []
        for assignment in self.assignments:
            if assignment.course is None:
                assignment.course = id_


class MockRoster:
    """A mock of a codePost course roster."""

    def __init__(self, id_=None, *, students=None):
        self.id = id_
        self.students = students or []


class MockAssignment:
    """A mock of a codePost assignment."""

    def __init__(
        self,
        id_=None,
        name=None,
        *,
        course_id=None,
        categories=None,
        submissions=None,
        num_submissions=0,
    ):
        self.id = id_
        self.course = course_id
        self.name = name
        self.rubricCategories = categories or []
        if submissions is not None:
            self._submissions = submissions
        else:
            self._submissions = [
                MockSubmission(
                    id_=i, assignment_id=id_, students=[f"student{i}"]
                )
                for i in range(num_submissions)
            ]

    def list_submissions(self, id=None, student=None, grader=None):
        # pylint: disable=redefined-builtin
        # use the same signature as the codePost method
        return self._submissions


class MockRubricCategory:
    """A mock of a codePost rubric category."""

    def __init__(self, name, point_limit=None, *, comments=None):
        self.name = name
        self.pointLimit = point_limit
        self.rubricComments = comments or []


class MockRubricComment:
    """A mock of a codePost rubric comment."""

    _comment_id = itertools.count()

    def __init__(
        self,
        name=None,
        point_delta=0,
        *,
        text="",
        explanation="",
        instructions="",
        is_template=False,
    ):
        self.id = next(MockRubricComment._comment_id)
        self.name = name
        self.pointDelta = point_delta
        self.text = text
        self.explanation = explanation
        self.instructionText = instructions
        self.templateTextOn = is_template


class MockSubmission:
    """A mock of a codePost submission."""

    def __init__(self, id_=None, *, assignment_id=None, students=None):
        self.id = id_
        self.assignment = assignment_id
        self.students = students


# =============================================================================


class MockClient:
    """A mock of a gspread OAuth Client."""

    def __init__(self, expired=True, spreadsheet_success=False):
        self._expired = expired
        self._spreadsheet_success = spreadsheet_success

    def _check_expired(self):
        if self._expired:
            raise google.auth.exceptions.RefreshError

    def list_spreadsheet_files(self):
        self._check_expired()

    def open(self, sheet_name):
        self._check_expired()
        if not self._spreadsheet_success:
            raise gspread.SpreadsheetNotFound(sheet_name)
        return MockSpreadsheet(sheet_name)


class MockSpreadsheet:
    """A mock of a gspread spreadsheet."""

    def __init__(self, name=None):
        self._name = name
        self._worksheets = {}
        self._times_called = {
            "add_worksheet": 0,
            "del_worksheet": 0,
            "del_worksheets": 0,
        }

    def times_called(self, method_name):
        if method_name not in self._times_called:
            raise KeyError(method_name)
        return self._times_called[method_name]

    @staticmethod
    def track_times_called(method):
        def wrapper(self, *args, **kwargs):
            # pylint: disable=protected-access
            self._times_called[method.__name__] += 1
            return method(self, *args, **kwargs)

        return wrapper

    def batch_update(self, body):
        """Sends a lower-level batch update request, but for this mock
        does nothing.
        """

    def num_worksheets(self):
        return len(self._worksheets)

    def worksheets(self):
        return list(self._worksheets.values())

    def get_worksheet_titles(self):
        return list(self._worksheets.keys())

    def _set_worksheet_indices(self):
        for i, worksheet in enumerate(self._worksheets.values()):
            worksheet.index = i

    def add_mock_worksheets(self, worksheets):
        for worksheet in worksheets:
            if not isinstance(worksheet, MockWorksheet):
                raise TypeError("worksheet must have type `MockWorksheet`")
            title = worksheet.title
            if title in self._worksheets:
                raise ValueError(f"repeated title: {title}")
            self._worksheets[title] = worksheet
        self._set_worksheet_indices()

    @track_times_called
    def add_worksheet(self, title="Sheet", rows=1, cols=1, index=None):
        count = 1
        ws_title = title
        while ws_title in self._worksheets:
            ws_title = f"{title} {count}"
            count += 1
        worksheet = MockWorksheet(self, title, rows=rows, cols=cols)
        self._worksheets[title] = worksheet
        self._set_worksheet_indices()
        return worksheet

    @track_times_called
    def del_worksheet(self, worksheet):
        self._worksheets.pop(worksheet.title)
        self._set_worksheet_indices()

    @track_times_called
    def del_worksheets(self, worksheets):
        for worksheet in worksheets:
            self._worksheets.pop(worksheet.title)
        self._set_worksheet_indices()


class MockWorksheet:
    """A mock of a gspread worksheet."""

    _worksheet_id = itertools.count()

    def __init__(self, spreadsheet, title, rows=1, cols=1, values=None):
        self.id = next(MockWorksheet._worksheet_id)
        self.spreadsheet = spreadsheet
        self.title = title
        self.index = None
        self.frozen_row_count = 0
        self.frozen_col_count = 0

        # set the values and fill it out with the appropriate number of
        # rows and columns
        self._values = []
        if values is not None:
            self._values = values
        if len(self._values) < rows:
            self._values += [[] for _ in range(rows - len(self._values))]
        for row in self._values:
            if len(row) < cols:
                row += [None for _ in range(cols - len(row))]

        self.row_count = len(self._values)
        self.col_count = len(self._values[0])

    def update_title(self, title):
        self.title = title

    def acell(self, label, value_render_option=ValueRenderOption.formatted):
        row, col = a1_to_rowcol(label)
        return MockCell(self._values[row - 1][col - 1])

    def get_values(self, range_name=None, **kwargs):
        return self._values

    def get_all_records(self, empty2zero=False, head=1, default_blank=""):
        headers = self._values[head - 1]
        seen = set()
        for header in headers:
            if header in seen:
                raise gspread.GSpreadException("head row has duplicate values")
            seen.add(header)

        records = []
        for row in self._values[head:]:
            records.append(dict(zip(headers, row)))
        return records

    def update(self, range_name, values, **kwargs):
        # assumes this is always called as `update(range, values)`
        grid_range = a1_range_to_grid_range(range_name)
        start_row = grid_range.get("startRowIndex", 0)
        start_col = grid_range.get("startColumnIndex", 0)

        row_diff = (start_row + len(values)) - (self.row_count)
        if row_diff > 0:
            self._values += [[] for _ in range(row_diff)]
        num_cols = max(map(len, values))
        for row in self._values:
            col_diff = (start_col + num_cols) - (len(row))
            if col_diff > 0:
                row += [None for _ in range(col_diff)]
        for r, row in enumerate(values):
            for c, value in enumerate(row):
                self._values[start_row + r][start_col + c] = value

        self.row_count = len(self._values)
        self.col_count = len(self._values[0])


class MockCell:
    """A mock of a gspread cell."""

    def __init__(self, value):
        self.value = value
