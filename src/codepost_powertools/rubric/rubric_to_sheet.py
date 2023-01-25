"""
Exports a codePost rubric to a Google Sheet.
"""

# To edit the headers of the sheet, see:
# - :class:`Headers`
# To edit the formatting of the sheet, see:
# - :func:`_assignment_worksheet_format_kwargs`
# To edit the information displayed on the sheet, see:
# - :func:`_format_is_template`
# - :func:`_get_codepost_rubric_as_data_rows`
# - :meth:`InstanceCounts.as_data_row`

# =============================================================================

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple, Union

import click
import cloup
import gspread

from codepost_powertools._utils import _get_logger, with_pluralized
from codepost_powertools._utils.cli_utils import (
    Stopwatch,
    click_flag,
    convert_course,
    log_start_end,
)
from codepost_powertools._utils.gspread_utils import (
    Color,
    Worksheet,
    add_worksheet,
    authenticate_client,
    col_index_to_letter,
    open_spreadsheet,
)
from codepost_powertools.rubric._cli_group import group
from codepost_powertools.utils.codepost_utils import TIER_PATTERN, with_course
from codepost_powertools.utils.cptypes import Assignment, Course

# =============================================================================

__all__ = ("export_rubric",)

# =============================================================================

GREEN: Color = (109, 177, 84)
WHITE: Color = (255, 255, 255)

# =============================================================================


class Headers:
    """The headers of an assignment sheet.

    This class includes helper functions to get column letters or ranges
    from given headers.

    .. versionadded:: 0.2.0
    """

    @dataclass(frozen=True, kw_only=True)
    class Header:
        """Represents a header.

        .. versionadded:: 0.2.0
        """

        name: str
        width: Optional[int] = None

    _headers = {
        "IDS": Header(name=""),
        "CATEGORY_NAME": Header(name="Category", width=100),
        "CATEGORY_POINTS": Header(name="Max", width=50),
        "COMMENT_NAME": Header(name="Name", width=150),
        "COMMENT_TIER": Header(name="Tier", width=50),
        "COMMENT_POINTS": Header(name="Points", width=75),
        "COMMENT_CAPTION": Header(name="Grader Caption", width=200),
        "COMMENT_EXPLANATION": Header(name="Explanation", width=650),
        "COMMENT_INSTRUCTIONS": Header(name="Instructions", width=300),
        "COMMENT_IS_TEMPLATE": Header(name="Template?", width=100),
    }
    _instance_headers = {
        "INSTANCES_TOTAL": Header(name="Instances", width=75),
        "INSTANCES_UPVOTES": Header(name="Upvote", width=75),
        "INSTANCES_UPVOTES_PERCENT": Header(name="", width=75),
        "INSTANCES_DOWNVOTES": Header(name="Downvote", width=75),
        "INSTANCES_DOWNVOTES_PERCENT": Header(name="", width=75),
    }

    def __init__(self, include_instances: bool):
        """Initializes the headers with or without the "instances"
        columns.

        Args:
            include_instances (|bool|): Whether to include the
                "instances" columns.

        .. versionadded:: 0.2.0
        """
        self._include_instances = include_instances
        # maps: header -> index
        self._indices: Dict[str, int] = {}
        # maps: header -> offset -> col letter
        self._letters: Dict[str, Dict[int, str]] = {}
        self._names: List[str] = []
        self._col_widths: List[Tuple[str, int]] = []
        self._last_col_letter: Optional[str] = None

        def add_headers(headers):
            for name, header in headers.items():
                i = len(self._indices) + 1
                self._indices[name] = i
                col_letter = col_index_to_letter(i)
                self._last_col_letter = col_letter
                self._letters[name] = {0: col_letter}
                self._names.append(header.name)
                if header.width is not None:
                    self._col_widths.append((col_letter, header.width))

        add_headers(self._headers)
        if include_instances:
            add_headers(self._instance_headers)

    @property
    def include_instances(self) -> bool:
        """Whether to include the "instances" columns.

        .. versionadded:: 0.2.0
        """
        return self._include_instances

    @property
    def names(self) -> List[str]:
        """The header names as a list.

        .. versionadded:: 0.2.0
        """
        return self._names

    @property
    def col_widths(self) -> List[Tuple[str, int]]:
        """The widths of the header columns, in the format for
        :func:`~codepost_powertools._utils.gspread_utils.display_on_worksheet`.

        .. versionadded:: 0.2.0
        """
        return self._col_widths

    def index(self, header: str) -> int:
        """Returns the index of the given header (1-indexed).

        Args:
            header (|str|): The header.

        Returns:
            |int|: The index.

        .. versionadded:: 0.2.0
        """
        return self._indices[header]

    def _split_row(self, row: Union[str, int]) -> Tuple[str, str]:
        """Splits a row into the section before and after the colon.

        Args:
            row (``Union[str, int]``)

        :rtype: ``Tuple[str, str]``

        .. versionadded:: 0.2.0
        """
        start_row, sep, end_row = str(row).partition(":")
        if sep == "":
            end_row = start_row
        return start_row, end_row

    def col_letter(
        self, header: str, *, offset: int = 0, row: Union[str, int] = ""
    ) -> str:
        """Returns the column letter of the given header.

        Args:
            header (|str|): The header.
            offset (|int|): An offset to add to the index.
            row (``Union[str, int]``): A row to include at the end.

        Returns:
            |str|: The column letter.

        .. versionadded:: 0.2.0
        """
        if offset not in self._letters[header]:
            # cache the letter with offset
            self._letters[header][offset] = col_index_to_letter(
                self._indices[header] + offset
            )
        col_letter = self._letters[header][offset]
        return f"{col_letter}{row}"

    def col_range(
        self,
        start_header: str,
        end_header: Optional[str] = None,
        *,
        offset: int = 0,
        row: Union[str, int] = "",
    ) -> str:
        """Returns a column range between the given headers.

        If ``end_header`` isn't given, it will default to the last
        header column.

        Args:
            start_header (|str|): The start header.
            end_header (|str|): The end header.
            offset (|int|): An offset to add to the entire range.
            row (``Union[str, int]``): A row to include at the end.

        Returns:
            |str|: The column range.

        .. versionadded:: 0.2.0
        """
        start_col = self.col_letter(start_header, offset=offset)
        if end_header is None:
            end_col = self._last_col_letter
        else:
            end_col = self.col_letter(end_header, offset=offset)
        start_row, end_row = self._split_row(row)
        return f"{start_col}{start_row}:{end_col}{end_row}"

    def col_width(
        self,
        header: str,
        width: int = 1,
        *,
        offset: int = 0,
        row: Union[str, int] = "",
    ) -> str:
        """Returns a column range of the given width starting at the
        given header.

        Args:
            header (|str|): The header.
            width (|int|): The range width.
            offset (|int|): An offset to add to the entire range.
            row (``Union[str, int]``): A row to include at the end.

        Returns:
            |str|: The column range.

        .. versionadded:: 0.2.0
        """
        start_col = self.col_letter(header, offset=offset)
        end_col = self.col_letter(header, offset=offset + width - 1)
        start_row, end_row = self._split_row(row)
        return f"{start_col}{start_row}:{end_col}{end_row}"


#: The row number of the header row.
HEADER_ROW = 2


def _assignment_worksheet_format_kwargs(headers: Headers) -> Dict[str, Any]:
    """Returns the worksheet format kwargs.

    Args:
        headers (:class:`Headers`): The headers.

    Returns:
        ``Dict[str, Any]``: The kwargs.

    .. versionadded:: 0.2.0
    """
    kwargs = {
        # freeze rows up to the header row
        "freeze_rows": HEADER_ROW,
        # freeze columns up to the comment name
        "freeze_cols": headers.index("COMMENT_NAME"),
        "col_widths": headers.col_widths,
        "range_formats": [
            # header: everything after ids column
            (
                headers.col_letter("IDS", offset=1, row=f"1:{HEADER_ROW}"),
                {
                    "bold": True,
                    "background_color": GREEN,
                    "text_color": WHITE,
                },
            ),
            (
                headers.col_letter(
                    "IDS", offset=1, row=f"{HEADER_ROW}:{HEADER_ROW}"
                ),
                {"text_align": "CENTER"},
            ),
            # ids column
            (
                headers.col_letter("IDS"),
                {"vertical_align": "MIDDLE"},
            ),
            # rubric content (everything after the headers)
            (
                headers.col_range(
                    "IDS",
                    end_header=None,
                    offset=1,
                    row=f"{HEADER_ROW + 1}:",
                ),
                {"vertical_align": "MIDDLE", "wrap": "WRAP"},
            ),
        ],
        "hide_cols": [
            headers.col_letter(header)
            for header in (
                "IDS",
                "COMMENT_EXPLANATION",
            )
        ],
    }
    if headers.include_instances:
        # merge instance upvotes/downvotes headers and add
        # percentage formatting
        PERCENT_FORMAT = {"fmt_type": "PERCENT", "pattern": "0.0%"}
        merge_ranges = []
        number_formats = []
        for header in ("UPVOTES", "DOWNVOTES"):
            merge_ranges.append(
                headers.col_width(
                    f"INSTANCES_{header}", width=2, row=HEADER_ROW
                )
            )
            number_formats.append(
                (
                    headers.col_width(f"INSTANCES_{header}_PERCENT"),
                    PERCENT_FORMAT,
                )
            )
        kwargs["merge_ranges"] = merge_ranges
        kwargs["number_formats"] = number_formats
    return kwargs


# =============================================================================


def _get_worksheets(
    sheet: gspread.Spreadsheet,
    assignments: Iterable[Assignment],
    *,
    wipe: bool = False,
    replace: bool = False,
    log: bool = False,
) -> Dict[str, Worksheet]:
    """Gets the worksheets for the given assignments.

    If ``wipe`` is True, the entire spreadsheet will be wiped and new
    worksheets will be created for each assignment.

    If ``replace`` is True, existing worksheets that correspond with the
    requested assignments will be replaced. Otherwise, new worksheets
    will be created with number suffixes to avoid naming conflicts.

    Args:
        sheet (|gspread Spreadsheet|): The spreadsheet.
        assignments (``Iterable`` [|Assignment|_]): The assignments.
        wipe (|bool|): Whether to wipe all the existing worksheets.
        replace (|bool|): Whether to replace the existing assignment
            worksheets.
        log (|bool|): Whether to show log messages.

    Returns:
        ``Dict`` [|str|, |Worksheet|]:
            A mapping from the assignment names to their corresponding
            worksheets.

    .. versionadded:: 0.2.0
    """
    _logger = _get_logger(log)

    existing = sheet.worksheets()
    # add a temporary worksheet so we don't have to deal with edge case
    # of removing all the sheets (which is an error)
    temp = add_worksheet(sheet)

    existing_assignment_worksheets = {}

    if wipe:
        # delete all current sheets
        num_existing = len(existing)
        _logger.debug(
            "Wiping {}", with_pluralized(num_existing, "existing worksheet")
        )
        for _ in range(num_existing):
            sheet.del_worksheet(existing.pop())
    elif replace:
        # get worksheets for each assignment
        for index, worksheet in enumerate(existing):
            # assume the first cell contains the assignment id
            a1 = Worksheet(worksheet).get_cell("A1").value
            if a1 is not None and a1.isdigit():
                existing_assignment_worksheets[int(a1)] = (worksheet, index)

    _logger.info("Getting worksheets for each assignment")
    found = 0
    created = 0

    worksheets = {}

    for assignment in assignments:
        a_id = assignment.id
        a_name = assignment.name

        this_worksheet = None

        if replace and a_id in existing_assignment_worksheets:
            _logger.debug("Replacing worksheet for assignment {!r}", a_name)
            found += 1
            # TODO: actually replace existing worksheet rather than
            #   deleting and adding new worksheet in its place
            worksheet, index = existing_assignment_worksheets.pop(a_id)
            title = worksheet.title
            sheet.del_worksheet(worksheet)
            # add new worksheet in same place
            this_worksheet = Worksheet(
                add_worksheet(sheet, title=title, index=index)
            )
        else:
            created += 1
            # create new worksheet
            this_worksheet = Worksheet(add_worksheet(sheet, title=a_name))

        # format the sheet with default font
        this_worksheet.format_cell("A1", font_family="Fira Code", update=True)

        worksheets[a_name] = this_worksheet

    # remove temp worksheet
    sheet.del_worksheet(temp)

    if log:
        actions_to_log = []
        if found > 0:
            actions_to_log.append(
                "found {}".format(with_pluralized(found, "worksheet"))
            )
        if created > 0:
            actions_to_log.append(
                "created {}".format(with_pluralized(created, "worksheet"))
            )
        if len(actions_to_log) > 0:
            action_to_log = " and ".join(actions_to_log)
            # capitalize the first letter
            # `str.capitalize` will also make all other letters
            # lowercase, which is undesired and unnecessary here
            action_to_log = action_to_log[0].upper() + action_to_log[1:]
            _logger.debug(action_to_log)

    return worksheets


# =============================================================================


def _format_is_template(is_template: bool) -> str:
    """Formats the "is template" field depending on the boolean value.

    Args:
        is_template (|bool|)

    :rtype: |str|

    .. versionadded:: 0.2.0
    """
    return "Yes" if is_template else ""


def _get_codepost_rubric_as_data_rows(
    assignment: Assignment, *, log: bool = False
) -> Dict[int, List[List[Any]]]:
    """Gets the codePost rubric for the given assignment as data rows.

    For each assignment, the order is: comment id, category name,
    category points, name, tier, points, text, explanation, instruction
    is template.

    Args:
        assignment (|Assignment|_): The assignment.
        log (|bool|): Whether to show log messages.

    Returns:
        ``Dict[int, List[List[Any]]]``:
            A mapping from comment ids to their corresponding data row.

    .. versionadded:: 0.2.0
    """
    _logger = _get_logger(log)

    a_name = assignment.name

    _logger.debug("Getting codePost rubric for assignment {!r}", a_name)

    rubric_data = {}

    for category in assignment.rubricCategories:
        category_points = category.pointLimit
        if category_points is None:
            category_points = ""
        else:
            # flip the value
            category_points *= -1

        for comment in category.rubricComments:
            comment_id = comment.id

            # flip the value
            comment_points = -1 * comment.pointDelta
            text = comment.text

            # get tier if has it
            match = TIER_PATTERN.match(text)
            tier: Union[Literal[""], int]
            if match is None:
                tier = ""
            else:
                tier_digits, text = match.group("tier", "text")
                # unnecessary, since the values don't care about type and it's
                # guaranteed to be a string of digits already
                tier = int(tier_digits)

            rubric_data[comment_id] = [
                comment_id,
                category.name,
                category_points,
                comment.name,
                tier,
                comment_points,
                text,
                comment.explanation,
                comment.instructionText,
                _format_is_template(comment.templateTextOn),
            ]

    _logger.debug("Got all rubric comments for assignment {!r}", a_name)

    return rubric_data


# =============================================================================


@dataclass
class InstanceCounts:
    """Keeps track of the number of instances of a rubric comment.

    .. versionadded:: 0.2.0
    """

    #: The id of the comment these counts are for.
    comment_id: int
    #: The total instances.
    total: int = 0
    #: The number of upvotes this comment got.
    upvotes: int = 0
    #: The number of downvotes this comment got.
    downvotes: int = 0

    @property
    def upvote_percent(self) -> float:
        """The percentage of upvotes this comment got.

        .. versionadded:: 0.2.0
        """
        if self.total == 0:
            return 0
        return self.upvotes / self.total

    @property
    def downvote_percent(self) -> float:
        """The percentage of downvotes this comment got.

        .. versionadded:: 0.2.0
        """
        if self.total == 0:
            return 0
        return self.downvotes / self.total

    def as_data_row(self) -> List[float]:
        """Converts the instance counts into a data row.

        The order is: total, upvotes, percent upvotes, downvotes,
        percent downvotes.

        If the total is 0, only the total will be given.

        Returns:
            ``List[float]``: The data.

        .. versionadded:: 0.2.0
        """
        if self.total == 0:
            return [0]
        return [
            self.total,
            self.upvotes,
            self.upvote_percent,
            self.downvotes,
            self.downvote_percent,
        ]


def _count_comment_instances(
    assignment: Assignment, comment_ids: Iterable[int], *, log: bool = False
):
    """Counts the number of instances of each rubric comment for the
    given assignment.

    Args:
        assignment (|Assignment|_): The assignment.
        comment_ids (``Iterable[int]``): The rubric comment ids.
        log (|bool|): Whether to show log messages.

    Returns:
        ``Dict`` [|int|, :class:`InstanceCounts`]:
            A mapping from rubric comment ids to ``InstanceCounts``
            objects.

    .. versionadded:: 0.2.0
    """
    _logger = _get_logger(log)

    a_name = assignment.name

    _logger.debug("Counting comment instances for assignment {!r}", a_name)

    counts = {
        comment_id: InstanceCounts(comment_id) for comment_id in comment_ids
    }

    stopwatch = Stopwatch().start()

    for submission in assignment.list_submissions():
        for file in submission.files:
            for comment in file.comments:
                comment_id = comment.rubricComment
                if comment_id is None:
                    # not a rubric comment
                    continue
                counts[comment_id].total += 1

                # feedback votes
                feedback = comment.feedback
                if feedback == 0:
                    pass
                elif feedback == 1:
                    counts[comment_id].upvotes += 1
                elif feedback == -1:
                    counts[comment_id].downvotes += 1

    _logger.debug(
        "Counted all comment instances for assignment {!r}: {}",
        a_name,
        stopwatch.elapsed_str(),
    )

    return counts


# =============================================================================


@with_course
def export_rubric(
    course: Course,
    sheet_name: str,
    assignments: Iterable[str],
    *,
    wipe: bool = False,
    replace: bool = False,
    count_instances: bool = False,
    log: bool = False,
) -> Dict[str, bool]:
    """Exports a codePost rubric to a Google Sheet.

    Each assignment's rubric will be exported into a single worksheet of
    the given Google Sheet. If ``wipe`` is True, the entire sheet will
    be wiped first. If ``replace`` is True, whenever an assignment being
    exported sees an existing worksheet, it will replace that sheet with
    the current exported rubric.

    If ``count_instances`` is True, it will count the number of
    instances of each rubric comment. Note that this may be slow, since
    it will have to loop through all the applied comments in the
    assignment submissions.

    This function will return a mapping from assignment names to a bool
    representing whether the export for that assignment was successful.
    The keys for this mapping will come from ``assignments``.

    .. note::
       The Google Sheet must already exist. This function will not
       create it for you.

    Args:
        course (|CourseArg|): The course.
        sheet_name (|str|): The Google Sheet name.
        assignments (``Iterable[str]``): The names of the assignments to
            export.
        wipe (|bool|): Whether to wipe all the existing worksheets.
        replace (|bool|): Whether to replace the existing assignment
            worksheets.
        count_instances (|bool|): Whether to count the number of
            instances of each rubric comment.
        log (|bool|): Whether to show log messages.

    Returns:
        ``Dict[str, bool]``:
            A mapping from assignment names to whether the export was
            successful.

    .. versionadded:: 0.2.0
    """
    _logger = _get_logger(log)
    headers = Headers(count_instances)

    successes = {}
    for assignment_name in assignments:
        successes[assignment_name] = False

    if course is None:
        # course retrieval failed
        return successes

    if len(successes) == 0:
        _logger.error("No assignments to export")
        return successes

    _logger.debug("Getting assignments")
    course_assignments = {
        assignment.name: assignment for assignment in course.assignments
    }
    valid_assignments = {}
    for assignment_name in successes:
        if assignment_name not in course_assignments:
            _logger.warning(
                "Assignment {!r} not found in the course", assignment_name
            )
            continue
        valid_assignments[assignment_name] = course_assignments[
            assignment_name
        ]
    if len(valid_assignments) == 0:
        _logger.error("No assignments to export")
        return successes
    _logger.info(
        "Found {}", with_pluralized(len(valid_assignments), "assignment")
    )

    success, client = authenticate_client(log=log)
    if not success:
        return successes

    success, sheet = open_spreadsheet(client, sheet_name, log=log)
    if not success:
        return successes

    # get worksheets for each assignment
    worksheets = _get_worksheets(
        sheet, valid_assignments.values(), wipe=wipe, replace=replace, log=log
    )

    _logger.info("Exporting rubrics to spreadsheet")

    # maps: assignment name -> comment id -> comment data
    comment_ids = {}
    for assignment_name, assignment in valid_assignments.items():
        comments = _get_codepost_rubric_as_data_rows(assignment, log=log)
        comment_ids[assignment_name] = comments

        values = [
            [assignment.id, f"Assignment: {assignment_name}"],
            headers.names,
        ]
        values.extend(comments.values())

        _logger.debug(
            "Displaying rubric comments for assignment {!r}", assignment_name
        )
        worksheet = worksheets[assignment_name]
        worksheet.set_values(values)
        worksheet.bulk_format(
            **_assignment_worksheet_format_kwargs(headers), update=True
        )

        successes[assignment_name] = True

    if count_instances:
        _logger.info("Counting instances of all rubric comments")
        stopwatch = Stopwatch().start()

        for assignment_name, assignment in valid_assignments.items():
            if not successes[assignment_name]:
                _logger.warning(
                    "Skipping assignment {!r}: export failed", assignment_name
                )
                continue

            counts = _count_comment_instances(
                assignment, comment_ids[assignment_name].keys(), log=log
            )
            values = [
                instance_count.as_data_row()
                for instance_count in counts.values()
            ]

            _logger.debug(
                "Displaying instances for assignment {!r}", assignment_name
            )
            worksheets[assignment_name].set_values(
                values,
                range_a1=headers.col_letter(
                    "INSTANCES_TOTAL", row=HEADER_ROW + 1
                ),
            )

        _logger.info(
            "Counted instances of all rubric comments: {}",
            stopwatch.elapsed_str(),
        )

    return successes


@group.command(
    name="export",
    help=__doc__,
    paired_func=":func:`codepost_powertools.rubric.export_rubric`",
)
@click.argument("course_name", type=str, required=True)
@click.argument("course_period", type=str, required=True)
@click.argument("sheet_name", type=str, required=True)
@cloup.argument(
    "assignments",
    type=str,
    required=True,
    nargs=-1,
    help="The names of the assignments to export. At least 1 is required.",
)
@click_flag("-w", "--wipe", help="Wipe all the existing worksheets.")
@click_flag(
    "-r", "--replace", help="Replace the existing assignment worksheets."
)
@click_flag(
    "-ci",
    "--count-instances",
    help="Count the instances of rubric comments. Warning: May be slow.",
)
@log_start_end
@convert_course
def export_cmd(**kwargs):
    """
    .. versionadded:: 0.2.0
    """
    export_rubric(**kwargs)
