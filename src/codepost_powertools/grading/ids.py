"""
ids.py
Creates a mapping between student emails and submission ids.
"""

# =============================================================================

from typing import Dict, Optional

import click

from codepost_powertools._utils import _get_logger
from codepost_powertools._utils.cli_utils import (
    cb_validate_csv,
    convert_course,
    log_start_end,
)
from codepost_powertools._utils.file_io import get_path, save_csv, validate_csv
from codepost_powertools._utils.types import (
    ParamPathOut,
    PathLike,
    SuccessOrNone,
)
from codepost_powertools.grading._cli_group import group
from codepost_powertools.utils.codepost_utils import (
    get_course_roster,
    with_course_and_assignment,
)
from codepost_powertools.utils.cptypes import Assignment, Course

# =============================================================================

__all__ = ("get_ids_mapping",)

# =============================================================================

DEFAULT_MAPPING_FILENAME = "ids.csv"

# =============================================================================


@with_course_and_assignment
def get_ids_mapping(
    course: Course,
    assignment: Assignment,
    *,
    include_all_students: bool = False,
    save_file: bool | PathLike = False,
    log: bool = False,
) -> SuccessOrNone[Dict[str, int | None]]:
    """Returns a mapping between student emails and submission ids.

    The mapping will be from student emails to submission ids. If
    `include_all_students` is True, it will include the entire course
    roster of students, so the submission id will be None if a student
    does not have a submission for the given assignment. Otherwise, the
    only students included will be those with a submission for the given
    assignment.

    If `save_file` is truthy, a csv file will be saved with the columns
    `"submission_id"` and `"email"`. Since a submission may have
    multiple students, multiple rows may have the same `"submission_id"`
    value. Note that students without a submission do not appear in this
    file.

    If `save_file` is a path, that will be used. Otherwise (if
    `save_file` is True), the default file `"OUTPUT/ids.csv"` will be
    used.

    Args:
        course (CourseArg): The course.
        assignment (AssignmentArg): The assignment.
        include_all_students (bool): Whether to include the entire
            course roster of students.
        save_file (bool | PathLike): The csv file to save the data to.
        log (bool): Whether to show log messages.

    Returns:
        SuccessOrNone[Dict[str, int | None]]:
            The mapping from student emails to submission ids.

    Raises:
        ValueError: If `log` is False and `filepath` is not a csv file.
    """
    _logger = _get_logger(log)

    if course is None or assignment is None:
        # retrievals failed; do nothing
        return {}

    ids: Dict[str, Optional[int]] = {}

    if include_all_students:
        success, roster = get_course_roster(course, log=log)
        if not success:
            _logger.warning(
                "Could not fetch roster, so not including all students"
            )
        else:
            # populate the mapping with all the student emails
            for student in roster.students:
                ids[student] = None

    _logger.info("Getting assignment submissions")

    csv_data = []

    for submission in assignment.list_submissions():
        s_id = submission.id
        for student in submission.students:
            ids[student] = s_id
            csv_data.append(
                {
                    "submission_id": s_id,
                    "email": student,
                }
            )

    save_data_path = None
    if save_file:
        if save_file is True:
            save_data_path = DEFAULT_MAPPING_FILENAME
        else:
            success = validate_csv(save_file, log=log)
            if not success:
                _logger.warning("Not saving to a file")
            else:
                save_data_path = save_file

    if save_data_path is not None:
        success, filepath = get_path(
            filename=save_data_path,
            course=course,
            assignment=assignment,
            log=log,
        )
        if success:
            save_csv(csv_data, filepath, description="ids", log=log)

    return ids


# =============================================================================


@group.command(
    "ids", help="Creates a mapping between student emails and submission ids."
)
@click.argument("course_name", type=str, required=True)
@click.argument("course_period", type=str, required=True)
@click.argument("assignment", type=str, required=True)
@click.option(
    "-f",
    "--file",
    "save_file",
    type=ParamPathOut,
    default=DEFAULT_MAPPING_FILENAME,
    show_default=True,
    callback=cb_validate_csv,
    help="A filename to save the csv data.",
)
@log_start_end
@convert_course
def ids_cmd(**kwargs):
    get_ids_mapping(**kwargs)
