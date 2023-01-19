"""
Mock classes for testing.
"""

# =============================================================================

import re
from collections import defaultdict

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
        for msg in self._logs[level]:
            if exact:
                if msg == pattern:
                    return True
            else:
                match = re.search(pattern, msg)
                if match is not None:
                    return True
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
        submissions=None,
        num_submissions=0,
    ):
        self.id = id_
        self.course = course_id
        self.name = name
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


class MockSubmission:
    """A mock of a codePost submission."""

    def __init__(self, id_=None, *, assignment_id=None, students=None):
        self.id = id_
        self.assignment = assignment_id
        self.students = students
