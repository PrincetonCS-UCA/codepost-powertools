"""
Wrapper classes around |gspread Spreadsheet| and |gspread Worksheet|.
"""
# pylint: disable=too-many-public-methods

# Spreadsheet batch updating:
# https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/batchUpdate
# https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/request

# Note that functions and methods in this module raise all exceptions,
# regardless of whether ``log`` is True or not.

# Note that this module does not get tested, since mostly everything is
# either a thin wrapper around a ``gspread`` function or class, or makes
# direct requests to the Google Sheets API.

# =============================================================================

from __future__ import annotations

from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Tuple,
    Union,
)

import gspread
from gspread.utils import a1_range_to_grid_range as gridrange
from gspread.utils import column_letter_to_index, rowcol_to_a1
from typing_extensions import NotRequired, Required, TypedDict

# =============================================================================

__all__ = (
    "Color",
    "Spreadsheet",
    "col_letter_to_index",
    "col_index_to_letter",
    "Worksheet",
)

# =============================================================================

MAX_RGB = 255

#: An RGB tuple representing a color.
Color = Tuple[int, int, int]


def _get_color_dict(color: Color) -> Dict[str, float]:
    """Returns a dict representing the given color on a 0-1 scale."""
    return {
        key: color_val / MAX_RGB
        for key, color_val in zip(("red", "green", "blue"), color, strict=True)
    }


# =============================================================================


def _set_worksheet_title(func: Callable, title: str, *args, **kwargs):
    """Calls the given function with the given title and args.

    If a ``gspread.exceptions.APIError`` occurs due to a duplicate
    title, an incrementing value will be appended to the end of the
    title, and the function will be called until there is no longer a
    conflict.

    .. versionadded:: 0.2.0
    """
    try:
        return func(title=title, *args, **kwargs)
    except gspread.exceptions.APIError as ex:
        error = ex.response.json()["error"]
        if error["code"] == 400 and error["status"] == "INVALID_ARGUMENT":
            # error["message"] == (
            #     "Invalid requests[0].addSheet: A sheet with the name "
            #     '"{title}" already exists. Please enter another name.'
            # )
            pass
        else:
            raise
    count = 1
    while True:
        try:
            return func(title=f"{title} {count}", *args, **kwargs)
        except gspread.exceptions.APIError:
            count += 1


# =============================================================================


class Spreadsheet(gspread.Spreadsheet):
    """A wrapper class around |gspread Worksheet|.

    The :meth:`add_worksheet` method will keep trying to add a worksheet
    until there isn't a title conflict anymore.

    .. versionadded:: 0.2.0
    """

    def add_worksheet(
        self,
        title: str = "Sheet",
        *,
        rows: int = 1,
        cols: int = 1,
        index: Optional[int] = None,
    ) -> gspread.Worksheet:
        """Adds a new worksheet to the spreadsheet.

        If ``index`` is given, the worksheet will be inserted before the
        given 0-indexed index. For example, ``index = 0`` will insert
        the worksheet at the very beginning, and ``index = 1`` will
        insert the worksheet between the first and second sheets. If
        ``index`` is not given, the worksheet will be added at the end.

        Args:
            title (|str|): The title of the worksheet.
            rows (|int|): The number of rows.
            cols (|int|): The number of columns.
            index (|int|): The index position to insert the worksheet
                (0-indexed).

        Returns:
            |gspread Worksheet|: The worksheet.

        .. versionadded:: 0.2.0
        """
        # pylint: disable=arguments-differ
        return _set_worksheet_title(
            super().add_worksheet, title, rows=rows, cols=cols, index=index
        )


# =============================================================================


def col_letter_to_index(col: str) -> int:
    """Converts a column letter to its numerical index.

    Args:
        col (|str|): The column letter.

    Returns:
        |int|: The column number (1-indexed).

    Raises:
        gspread.exceptions.InvalidInputValue: If the input is invalid.

    .. versionadded:: 0.2.0
    """
    return column_letter_to_index(col)


def col_index_to_letter(col: int) -> str:
    """Converts a column index to its A1 notation letter.

    Args:
        col (|int|): The column number (1-indexed).

    Returns:
        |str|: The column letter.

    Raises:
        gspread.exceptions.InvalidInputValue: If the input is invalid.

    .. versionadded:: 0.2.0
    """
    if col <= 0:
        # similar format as `column_letter_to_index()``
        raise gspread.exceptions.InvalidInputValue(
            "invalid value: {}, must be a column 1-indexed number".format(col)
        )
    a1 = rowcol_to_a1(1, col)
    # remove the row number "1" at the end
    return a1[:-1]


# =============================================================================


class Worksheet:
    """A wrapper class around |gspread Worksheet|.

    .. versionadded:: 0.2.0

    .. data:: DEFAULT_ROW_HEIGHT
       :type: int
       :value: 21

       The default height of a row.

    .. data:: DEFAULT_COL_WIDTH
       :type: int
       :value: 120

       The default width of a column.

       .. note::
          Newly created spreadsheets will have column widths of 100, but
          the "Resize Column" popup says the default is 120.

    .. |DimensionRange| replace:: ``DimensionRange``
    """

    DEFAULT_ROW_HEIGHT: int = 21
    DEFAULT_COL_WIDTH: int = 120

    class DimensionRange(TypedDict):
        """A dimension range dict.

        .. versionadded:: 0.2.0
        """

        sheet_id: Required[int]
        dimension: Required[Literal["ROWS", "COLUMNS"]]
        startIndex: NotRequired[int]
        endIndex: NotRequired[int]

    def __init__(self, worksheet: gspread.Worksheet):
        """Initializes a Worksheet.

        Args:
            worksheet (|gspread Worksheet|): The worksheet returned from
                ``gspread``.

        .. versionadded:: 0.2.0
        """

        self._sheet: gspread.Spreadsheet = worksheet.spreadsheet
        self._worksheet: gspread.Worksheet = worksheet
        self._id: int = worksheet.id
        self._pending_requests: List[Dict] = []

    def __str__(self) -> str:
        return str(self._worksheet)

    def __repr__(self) -> str:
        return repr(self._worksheet)

    @property
    def title(self) -> str:
        """The worksheet title. Can be set.

        .. versionadded:: 0.2.0
        """
        return self._worksheet.title

    @title.setter
    def title(self, val: str):
        """Sets the worksheet title.

        .. versionadded:: 0.2.0
        """
        if val == self.title:
            return
        _set_worksheet_title(self._worksheet.update_title, val)

    @property
    def num_rows(self) -> int:
        """The number of rows in the worksheet.

        .. versionadded:: 0.2.0
        """
        return self._worksheet.row_count

    @property
    def num_cols(self) -> int:
        """The number of columns in the worksheet.

        .. versionadded:: 0.2.0
        """
        return self._worksheet.col_count

    @property
    def num_frozen_rows(self) -> int:
        """The number of frozen rows in the worksheet.

        .. versionadded:: 0.2.0
        """
        return self._worksheet.frozen_row_count

    @property
    def num_frozen_cols(self) -> int:
        """The number of frozen columns in the worksheet.

        .. versionadded:: 0.2.0
        """
        return self._worksheet.frozen_col_count

    def _get_dim_range(self, range_a1: str, dim: str) -> DimensionRange:
        """Returns the "DimensionRange" dict of a range.

        Args:
            range_a1 (|str|): The cell range in A1 notation.
            dim (|str|): The dimension.
                Choices: ``ROW``, ``COLUMN``.

        Returns:
            :data:`DimensionRange`: The dimension range dict.

        .. versionadded:: 0.2.0
        """

        if dim.lower() not in ("row", "column"):
            raise ValueError(f"Invalid dimension: {dim}")

        grid: Dict[str, int] = gridrange(range_a1)
        dim_range: Worksheet.DimensionRange = {
            "sheet_id": self._id,
            "dimension": dim.upper() + "S",  # type: ignore[typeddict-item]
        }

        dim_title = dim.title()
        if f"start{dim_title}Index" in grid:
            dim_range["startIndex"] = grid[f"start{dim_title}Index"]
        if f"end{dim_title}Index" in grid:
            dim_range["endIndex"] = grid[f"end{dim_title}Index"]

        return dim_range

    def _get_row_range(self, row: Union[str, int]) -> DimensionRange:
        """Returns the "DimensionRange" dict of a row.

        Args:
            row (``Union[str, int]``)

        :rtype: |DimensionRange|

        .. versionadded:: 0.2.0
        """
        return self._get_dim_range(str(row), "row")

    def _get_col_range(self, col: str) -> DimensionRange:
        """Returns the "DimensionRange" dict of a column.

        Args:
            col (|str|)

        :rtype: |DimensionRange|

        .. versionadded:: 0.2.0
        """
        return self._get_dim_range(col, "column")

    def update(self):
        """Updates the Google Sheet with the cached requests.

        Any method with ``update`` set to False will cache its request.
        If a method doesn't have the ``update`` keyword argument, its
        change takes effect immediately.

        The requests are processed in the given order. If an exception
        occurs, the rest of the requests are ignored. However, all the
        pending requests will be cleared, even if they weren't
        processed. (This is done so that interactive Python sessions can
        run into errors and still be used after.)

        .. versionadded:: 0.2.0
        """
        if len(self._pending_requests) == 0:
            return
        body = {"requests": self._pending_requests}
        try:
            self._sheet.batch_update(body)
        finally:
            self._pending_requests.clear()

    def get_cell(self, cell_a1: str) -> gspread.Cell:
        """Gets a cell of the worksheet.

        Args:
            cell_a1 (|str|): The cell in A1 notation.

        :rtype: |gspread Cell|

        .. versionadded:: 0.2.0
        """
        return self._worksheet.acell(cell_a1)

    def get_values(self) -> List[List[str]]:
        """Gets all the values of the worksheet as a 2D list.

        :rtype: ``List[List[str]]``

        .. versionadded:: 0.2.0
        """
        return self._worksheet.get_values()

    def get_records(
        self,
        empty2zero: bool = False,
        header_row: int = 1,
        default_blank: Any = "",
    ) -> List[Dict[str, Any]]:
        """Gets the values of the worksheet with the head row as keys.

        Args:
            empty2zero (|bool|): Whether empty cells are converted to 0.
            header_row (|int|): The header row number (1-indexed).
                All above rows will be ignored.
            default_blank (|Any|): The default value of blank cells.

        Returns:
            ``List[Dict[str, Any]]``:
                The row values with each row in the format:
                ``{ header1: val1, header2: val2, ... }``

        .. versionadded:: 0.2.0
        """
        return self._worksheet.get_all_records(
            empty2zero=empty2zero, head=header_row, default_blank=default_blank
        )

    def set_values(self, values: List[List[Any]], range_a1: str = "A1"):
        """Sets the values of the worksheet.

        The data will be inserted starting at the top-left cell of
        ``range_a1``. The size of the range itself doesn't matter, so a
        single value of the top-left cell of the data is enough.

        Args:
            values (``List[List[Any]]``): The values.
            range_a1 (|str|): The range in A1 notation.

        .. versionadded:: 0.2.0
        """
        self._worksheet.update(range_a1, values)

    def add_formula(
        self, range_a1: str, formula: str, *, update: bool = False
    ):
        """Adds a formula to the given cell(s).

        .. note::

           From the Sheets API `request documentation
           <https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/request#RepeatCellRequest>`_:

              The formula's ranges will automatically increment for each
              field in the range. For example, if writing a cell with
              formula ``=A1`` into range B2:C4, B2 would be ``=A1``, B3
              would be ``=A2``, B4 would be ``=A3``, C2 would be
              ``=B1``, C3 would be ``=B2``, C4 would be ``=B3``.

              To keep the formula's ranges static, use the ``$``
              indicator. For example, use the formula ``=$A$1`` to
              prevent both the row and the column from incrementing.

        Args:
            range_a1 (|str|): The cell range in A1 notation.
            formula (|str|): The formula.
            update (|bool|): Whether to update the worksheet.

        .. versionadded:: 0.2.0
        """

        if not formula.startswith("="):
            formula = f"={formula}"

        self._pending_requests.append(
            {
                "repeatCell": {
                    "range": gridrange(range_a1, sheet_id=self._id),
                    "cell": {
                        "userEnteredValue": {
                            "formulaValue": formula,
                        },
                    },
                    "fields": "userEnteredValue.formulaValue",
                }
            }
        )

        if update:
            self.update()

    def add_hyperlink(
        self,
        range_a1: str,
        link: str,
        text: Optional[str] = None,
        *,
        update: bool = False,
    ):
        """Adds a hyperlink to the given cell(s).

        .. note::

           ``text`` is a literal string to use as the label text, so any
           formulas in it will not be processed. To achieve that, use
           :meth:`add_formula` with the |HYPERLINK|_ formula.

           .. |HYPERLINK| replace:: ``HYPERLINK``
           .. _HYPERLINK: https://support.google.com/docs/answer/3093313?hl=en

        Args:
            range_a1 (|str|): The cell range in A1 notation.
            link (|str|): The link.
            text (|str|): The label text.
            update (|bool|): Whether to update the worksheet.

        .. versionadded:: 0.2.0
        """

        def escape_quotes(s: str) -> str:
            return s.replace('"', '\\"')

        formula = [f'=HYPERLINK("{link}"']
        if text is not None:
            formula.append(f', "{escape_quotes(str(text))}"')
        formula.append(")")
        self.add_formula(range_a1, "".join(formula), update=update)

    def resize(
        self, *, rows: Optional[int] = None, cols: Optional[int] = None
    ):
        """Resizes the worksheet.

        Non-positive values will be simply ignored (deleting all rows or
        columns is an error).

        Args:
            rows (|int|): The number of rows.
            cols (|int|): The number of columns.

        .. versionadded:: 0.2.0
        """
        if rows is not None and rows <= 0:
            rows = None
        if cols is not None and cols <= 0:
            cols = None
        self._worksheet.resize(rows, cols)

    def bulk_format(
        self,
        *,
        freeze_rows: Optional[int] = None,
        freeze_cols: Optional[int] = None,
        hide_rows: Optional[Iterable[Union[str, int]]] = None,
        hide_cols: Optional[Iterable[Union[str, int]]] = None,
        row_heights: Optional[Iterable[Tuple[Union[str, int], int]]] = None,
        col_widths: Optional[Iterable[Tuple[Union[str, int], int]]] = None,
        range_formats: Optional[Iterable[Tuple[str, Mapping]]] = None,
        number_formats: Optional[Iterable[Tuple[str, Mapping]]] = None,
        merge_ranges: Optional[Iterable[str]] = None,
        update: bool = False,
    ):
        """Formats the worksheet in bulk.

        For ``row_heights``, each tuple should be the row number and the
        height. For ``col_widths``, each tuple should be either the
        column number or letter and the width. Ranges are also accepted,
        such as ``"1:3"`` for rows or ``"A:E"`` for columns. Sizes less
        than 1 will be clamped to 1.

        For ``hide_rows``, each element should be the row number or a
        range of rows. For ``hide_cols``, each element should be the
        column number, column letter, or a range of columns.

        Args:
            freeze_rows (|int|): The number of rows to freeze.
            freeze_cols (|int|): The number of columns to freeze.
            hide_rows (``Iterable[Union[str, int]]``): The rows to hide.
            hide_cols (``Iterable[Union[str, int]]``): The columns to
                hide.
            row_heights (``Iterable[Tuple[Union[str, int], int]]``):
                The row heights to set.
            col_widths (``Iterable[Tuple[Union[str, int], int]]``):
                The column widths to set.
            range_formats (``Iterable[Tuple[str, Mapping]]``): Pairs of
                ranges and kwargs for :meth:`format_cell`.
            number_formats (``Iterable[Tuple[str, Mapping]]``): Pairs of
                ranges and kwargs for :meth:`format_number_cell`.
            merge_ranges (``Iterable[str]``): The ranges to merge.
            update (|bool|): Whether to update the worksheet.

        See the other methods for possible exceptions raised.

        .. versionadded:: 0.2.0
        """

        def col_to_a1(col: Union[str, int]) -> str:
            if isinstance(col, str):
                return col
            return col_index_to_letter(col)

        # freeze
        if freeze_rows is not None or freeze_cols is not None:
            # update immediately so that it crashes if everything is frozen
            self.freeze(rows=freeze_rows, cols=freeze_cols, update=update)

        # hide
        if hide_rows is not None:
            for row in hide_rows:
                self.hide_row(row)
            # update immediately so that it crashes if everything is hidden
            if update:
                self.update()
        if hide_cols is not None:
            for col in hide_cols:
                self.hide_col(col_to_a1(col))
            # update immediately so that it crashes if everything is hidden
            if update:
                self.update()

        # size
        if row_heights is not None:
            for row, height in row_heights:
                self.set_row_height(row, height)
        if col_widths is not None:
            for col, width in col_widths:
                self.set_col_width(col_to_a1(col), width)

        # formats
        if range_formats is not None:
            for range_a1, kwargs in range_formats:
                self.format_cell(range_a1, **kwargs)
        if number_formats is not None:
            for range_a1, kwargs in number_formats:
                self.format_number_cell(range_a1, **kwargs)

        # merge
        if merge_ranges is not None:
            for range_a1 in merge_ranges:
                self.merge_cells(range_a1)

        if update:
            self.update()

    def freeze(
        self,
        *,
        rows: Optional[int] = None,
        cols: Optional[int] = None,
        update: bool = False,
    ):
        """Freezes a number of rows or columns.

        Set the value to 0 to unfreeze all rows or columns.

        Negative values will be simply ignored.

        Args:
            rows (|int|): The number of rows to freeze.
            cols (|int|): The number of columns to freeze.
            update (|bool|): Whether to update the worksheet.

        Raises:
            gspread.exceptions.APIError: If all the visible rows or
                columns are frozen.

        .. versionadded:: 0.2.0
        """

        freezing = {}
        if rows is not None and rows >= 0:
            freezing["frozenRowCount"] = rows
        if cols is not None and cols >= 0:
            freezing["frozenColumnCount"] = cols
        if len(freezing) > 0:
            self._pending_requests.append(
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": self._id,
                            "gridProperties": freezing,
                        },
                        "fields": ",".join(
                            f"gridProperties.{f}" for f in freezing
                        ),
                    }
                }
            )

        if update:
            self.update()

    def _hide(self, dim_range: DimensionRange, *, update: bool = False):
        """Hides the given dimension range.

        Args:
            dim_range (|DimensionRange|): The dimension range.
            update (|bool|): Whether to update the worksheet.

        Raises:
            gspread.exceptions.APIError: If all the visible rows or
                columns are hidden.

        .. versionadded:: 0.2.0
        """

        self._pending_requests.append(
            {
                "updateDimensionProperties": {
                    "properties": {
                        "hiddenByUser": True,
                    },
                    "fields": "hiddenByUser",
                    "range": dim_range,
                }
            }
        )

        if update:
            self.update()

    def hide_row(self, row: Union[str, int], *, update: bool = False):
        """Hides the given row(s).

        Args:
            row (``Union[str, int]``): The row number or range.
            update (|bool|): Whether to update the worksheet.

        Raises:
            gspread.exceptions.APIError: If all the visible rows are
                hidden.

        .. versionadded:: 0.2.0
        """
        self._hide(self._get_row_range(row), update=update)

    def hide_col(self, col_a1: str, *, update: bool = False):
        """Hides the given column(s).

        Args:
            col_a1 (|str|): The column range in A1 notation.
            update (|bool|): Whether to update the worksheet.

        Raises:
            gspread.exceptions.APIError: If all the visible columns are
                hidden.

        .. versionadded:: 0.2.0
        """
        self._hide(self._get_col_range(col_a1), update=update)

    def _set_row_col_size(
        self, dim_range: DimensionRange, size: int, *, update: bool = False
    ):
        """Sets the size of the given dimension range.

        Sizes less than 1 will be clamped to 1.

        Args:
            dim_range (|DimensionRange|): The dimension range.
            size (|int|): The size.
            update (|bool|): Whether to update the worksheet.

        .. versionadded:: 0.2.0
        """

        self._pending_requests.append(
            {
                "updateDimensionProperties": {
                    "properties": {
                        "pixelSize": size,
                    },
                    "fields": "pixelSize",
                    "range": dim_range,
                }
            }
        )

        if update:
            self.update()

    def reset_row_height(self, row: Union[str, int], *, update: bool = False):
        """Resets the height of the given row(s) to
        :attr:`DEFAULT_ROW_HEIGHT`.

        Args:
            row (``Union[str, int]``): The row number or range.
            update (|bool|): Whether to update the worksheet.

        .. versionadded:: 0.2.0
        """
        self.set_row_height(row, self.DEFAULT_ROW_HEIGHT, update=update)

    def set_row_height(
        self, row: Union[str, int], height: int, *, update: bool = False
    ):
        """Sets the height of the given row(s).

        Sizes less than 1 will be clamped to 1.

        Args:
            row (``Union[str, int]``): The row number or range.
            height (|int|): The height.
            update (|bool|): Whether to update the worksheet.

        .. versionadded:: 0.2.0
        """
        self._set_row_col_size(self._get_row_range(row), height, update=update)

    def reset_col_width(self, col_a1: str, *, update: bool = False):
        """Resets the width of the given column(s) to
        :attr:`DEFAULT_COL_WIDTH`.

        Args:
            col_a1 (|str|): The column range in A1 notation.
            update (|bool|): Whether to update the worksheet.

        .. versionadded:: 0.2.0
        """
        self.set_col_width(col_a1, self.DEFAULT_COL_WIDTH, update=update)

    def set_col_width(self, col_a1: str, width: int, *, update: bool = False):
        """Sets the width of the given column(s).

        Sizes less than 1 will be clamped to 1.

        Args:
            col_a1 (|str|): The column range in A1 notation.
            width (|int|): The width.
            update (|bool|): Whether to update the worksheet.

        .. versionadded:: 0.2.0
        """
        self._set_row_col_size(
            self._get_col_range(col_a1), width, update=update
        )

    def merge_cells(self, range_a1: str, *, update: bool = False):
        """Merges the given range of cells.

        Args:
            range_a1 (|str|): The cell range in A1 notation.
            update (|bool|): Whether to update the worksheet.

        Raises:
            gspread.exceptions.APIError: If frozen and non-frozen cells
                are merged together.
            gspread.exceptions.APIError: If the merge fails, such as if
                the given range includes already merged cells.

        .. versionadded:: 0.2.0
        """

        self._pending_requests.append(
            {
                "mergeCells": {
                    "range": gridrange(range_a1, sheet_id=self._id),
                    "mergeType": "MERGE_ALL",
                }
            }
        )

        if update:
            self.update()

    def format_cell(
        self,
        range_a1: str,
        *,
        font_family: Optional[str] = None,
        bold: Optional[bool] = None,
        background_color: Optional[Color] = None,
        text_color: Optional[Color] = None,
        text_align: Optional[str] = None,
        vertical_align: Optional[str] = None,
        wrap: Optional[str] = None,
        update: bool = False,
    ):
        """Formats the given cell(s).

        Args:
            range_a1 (|str|): The cell range in A1 notation.
            font_family (|str|): The font family.
            bold (|bool|): Whether the text is bold.
            background_color (|Color|): The background color.
            text_color (|Color|): The text color.
            text_align (|str|): The text (horizontal) alignment type.
                Choices: ``LEFT``, ``CENTER``, ``RIGHT``.
            vertical_align (|str|): The vertical alignment type.
                Choices: ``TOP``, ``MIDDLE``, ``BOTTOM``.
            wrap (|str|): The wrapping type.
                Choices: ``OVERFLOW_CELL``, ``CLIP``, ``WRAP``.
            update (|bool|): Whether to update the Worksheet.

        .. versionadded:: 0.2.0
        """

        fmt: Dict[str, Any] = {}
        text_fmt: Dict[str, Any] = {}
        fields = []

        if font_family is not None:
            text_fmt["fontFamily"] = font_family
            fields.append("textFormat.fontFamily")
        if bold is not None:
            text_fmt["bold"] = bold
            fields.append("textFormat.bold")
        if background_color is not None:
            fmt["backgroundColor"] = _get_color_dict(background_color)
            fields.append("backgroundColor")
        if text_color is not None:
            text_fmt["foregroundColor"] = _get_color_dict(text_color)
            fields.append("textFormat.foregroundColor")
        if text_align is not None:
            fmt["horizontalAlignment"] = text_align
            fields.append("horizontalAlignment")
        if vertical_align is not None:
            fmt["verticalAlignment"] = vertical_align
            fields.append("verticalAlignment")
        if wrap is not None:
            fmt["wrapStrategy"] = wrap
            fields.append("wrapStrategy")

        if len(fields) == 0:
            if update:
                self.update()
            return

        if len(text_fmt) > 0:
            fmt["textFormat"] = text_fmt

        self._pending_requests.append(
            {
                "repeatCell": {
                    "range": gridrange(range_a1, sheet_id=self._id),
                    "cell": {
                        "userEnteredFormat": fmt,
                    },
                    "fields": ",".join(
                        f"userEnteredFormat.{f}" for f in fields
                    ),
                }
            }
        )

        if update:
            self.update()

    def format_number_cell(
        self,
        range_a1: str,
        fmt_type: str,
        pattern: str,
        *,
        update: bool = False,
    ):
        """Formats the given number cell(s).

        Args:
            range_a1 (|str|): The cell range.
            fmt_type (|str|): The format type.
                Choices: ``TEXT``, ``NUMBER``, ``PERCENT``,
                ``CURRENCY``, ``DATE``, ``TIME``, ``DATE_TIME``,
                ``SCIENTIFIC``.
            pattern (|str|): The formatting pattern.
                See https://developers.google.com/sheets/api/guides/formats.
            update (|bool|): Whether to update the worksheet.

        .. versionadded:: 0.2.0
        """

        self._pending_requests.append(
            {
                "repeatCell": {
                    "range": gridrange(range_a1, sheet_id=self._id),
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {
                                "type": fmt_type,
                                "pattern": pattern,
                            },
                        },
                    },
                    "fields": "userEnteredFormat.numberFormat",
                }
            }
        )

        if update:
            self.update()
