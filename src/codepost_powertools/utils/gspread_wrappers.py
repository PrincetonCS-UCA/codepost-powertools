"""
Wrapper classes around |gspread Spreadsheet| and |gspread Worksheet|.
"""
# pylint: disable=too-many-public-methods

# Note that functions and methods in this module raise all exceptions,
# regardless of whether ``log`` is True or not.

# Note that this module does not get tested, since mostly everything is
# either a thin wrapper around a ``gspread`` function or class, or makes
# direct requests to the Google Sheets API.

# =============================================================================

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, Union

import gspread
from gspread.utils import column_letter_to_index, rowcol_to_a1

from codepost_powertools.utils.sheets_api import (
    CellData,
    CellFormat,
    Color,
    ColorStyle,
    DimensionProperties,
    DimensionRange,
    ExtendedValue,
    GridProperties,
    GridRange,
    HorizontalAlign,
    MergeType,
    NumberFormat,
    NumberFormatType,
    SheetProperties,
    TextFormat,
    VerticalAlign,
    WrapStrategy,
)

# =============================================================================

__all__ = (
    "Spreadsheet",
    "col_letter_to_index",
    "col_index_to_letter",
    "Worksheet",
)

# =============================================================================


class Spreadsheet:
    """A wrapper class around |gspread Spreadsheet|.

    The :meth:`add_worksheet` method will change the specified title so
    that there is no worksheet title conflict.

    .. versionadded:: 0.2.0
    """

    def __init__(self, spreadsheet: gspread.Spreadsheet):
        """Initializes a spreadsheet.

        Args:
            spreadsheet (|gspread Spreadsheet|): The spreadsheet
                returned from ``gspread``.

        .. versionadded:: 0.2.0
        """
        self._spreadsheet = spreadsheet

    def __getattr__(self, name):
        # pass all attempted attribute accesses to the spreadsheet
        return getattr(self._spreadsheet, name)

    def get_valid_worksheet_title(
        self, title: str, *, fmt: str = "{title} {num}"
    ) -> str:
        """Returns a valid worksheet title from the given title.

        If the title already exists in the spreadsheet, a number will be
        appended to the end of the title and incremented until there is
        no longer a conflict.

        Args:
            title (|str|): The title.
            fmt (|str|): A template format for how the number is
                appended to the title. Requires ``"{title}"`` and
                ``"{num}"`` to be included in the string.

        Returns:
            |str|: The valid title.

        Raises:
            ValueError: If ``fmt`` is invalid.

        .. versionadded:: 0.2.0
        """
        if not ("{title}" in fmt and "{num}" in fmt):
            raise ValueError(
                '`fmt` is invalid: requires both "{title}" and "{num}"'
            )
        worksheet_titles = set(
            worksheet.title for worksheet in self._spreadsheet.worksheets()
        )
        ws_title = title
        count = 1
        while ws_title in worksheet_titles:
            ws_title = fmt.format(title=title, num=count)
            count += 1
        return ws_title

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
        return self._spreadsheet.add_worksheet(
            self.get_valid_worksheet_title(title), rows, cols, index
        )

    def del_worksheets(self, worksheets: Iterable[gspread.Worksheet]):
        """Deletes the given worksheets from the spreadsheet.

        Args:
            worksheets (``Iterable`` [|gspread Worksheet|]):
                The worksheets.

        .. versionadded:: 0.2.0
        """
        body = {
            "requests": [
                {"deleteSheet": {"sheetId": worksheet.id}}
                for worksheet in worksheets
            ]
        }
        return self._spreadsheet.batch_update(body)


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

ValidColor = Union[Color, Tuple[int, int, int], Tuple[float, float, float]]


class Worksheet:
    """A wrapper class around |gspread Worksheet|.

    .. versionadded:: 0.2.0
    """

    DEFAULT_ROW_HEIGHT: int = 21
    """The default height of a row."""

    DEFAULT_COL_WIDTH: int = 120
    """The default width of a column.

    .. note::
       Newly created spreadsheets will have column widths of 100, but
       the "Resize Column" popup says the default is 120.
    """

    def __init__(self, worksheet: gspread.Worksheet):
        """Initializes a worksheet.

        Args:
            worksheet (|gspread Worksheet|): The worksheet returned from
                ``gspread``.

        .. versionadded:: 0.2.0
        """

        self._spreadsheet = Spreadsheet(worksheet.spreadsheet)
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
        self._worksheet.update_title(
            self._spreadsheet.get_valid_worksheet_title(val)
        )

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

    def _get_grid_range(self, range_a1: str) -> GridRange:
        return GridRange.from_range(sheet_id=self._id, range_a1=range_a1)

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
            self._spreadsheet.batch_update(body)
        finally:
            self._pending_requests.clear()

    def get_value(self, cell_a1: str) -> Any:
        """Gets a value of the worksheet.

        Args:
            cell_a1 (|str|): The cell in A1 notation.

        :rtype: |Any|

        .. versionadded:: 0.2.0
        """
        return self._worksheet.acell(cell_a1).value

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

        cell_data = CellData(user_entered_value=ExtendedValue.formula(formula))
        update_request = cell_data.updateRequest(
            self._get_grid_range(range_a1)
        )
        self._pending_requests.append(update_request)

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

        if not (rows is None and cols is None):
            self._pending_requests.append(
                SheetProperties(
                    sheet_id=self._id,
                    grid_properties=GridProperties(
                        frozen_row_count=rows, frozen_col_count=cols
                    ),
                ).updateRequest()
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
            DimensionProperties(hidden_by_user=True).updateRequest(dim_range)
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
        self._hide(
            DimensionRange.rows(sheet_id=self._id, range_a1=str(row)),
            update=update,
        )

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
        self._hide(
            DimensionRange.cols(sheet_id=self._id, range_a1=col_a1),
            update=update,
        )

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
            DimensionProperties(pixel_size=size).updateRequest(dim_range)
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
        self._set_row_col_size(
            DimensionRange.rows(sheet_id=self._id, range_a1=str(row)),
            height,
            update=update,
        )

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
            DimensionRange.cols(sheet_id=self._id, range_a1=col_a1),
            width,
            update=update,
        )

    def merge_cells(
        self,
        range_a1: str,
        *,
        merge_type: MergeType = MergeType.MERGE_ALL,
        update: bool = False,
    ):
        """Merges the given range of cells.

        Args:
            range_a1 (|str|): The cell range in A1 notation.
            merge_type (|MergeType|): The merge type.
            update (|bool|): Whether to update the worksheet.

        Raises:
            gspread.exceptions.APIError: If frozen and non-frozen cells
                are merged together.
            gspread.exceptions.APIError: If the merge fails, such as if
                the given range includes already merged cells.

        .. versionadded:: 0.2.0
        """

        self._pending_requests.append(
            self._get_grid_range(range_a1).mergeRequest(merge_type=merge_type)
        )

        if update:
            self.update()

    def format_cell(
        self,
        range_a1: str,
        *,
        font_family: Optional[str] = None,
        font_size: Optional[int] = None,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        strikethrough: Optional[bool] = None,
        underline: Optional[bool] = None,
        background_color: Optional[ValidColor] = None,
        text_color: Optional[ValidColor] = None,
        text_align: Optional[HorizontalAlign] = None,
        vertical_align: Optional[VerticalAlign] = None,
        wrap: Optional[WrapStrategy] = None,
        update: bool = False,
    ):
        """Formats the given cell(s).

        Args:
            range_a1 (|str|): The cell range in A1 notation.
            font_family (|str|): The font family.
            font_size (|int|): The font size.
            bold (|bool|): Whether the text is bold.
            italic (|bool|): Whether the text is in italics.
            strikethrough (|bool|): Whether the text has a
                strikethrough.
            underline (|bool|): Whether the text is has an underline.
            background_color(|ValidColor|): The background color.
            text_color (|ValidColor|): The text color.
            text_align (|HorizontalAlign|): The text (horizontal)
                alignment type.
            vertical_align (|VerticalAlign|): The vertical alignment
                type.
            wrap (|WrapStrategy|): The wrapping type.
            update (|bool|): Whether to update the worksheet.

        .. |ValidColor| replace::
           |Color| or
           ``Tuple[int, int, int]`` or
           ``Tuple[float, float, float]``

        .. versionadded:: 0.2.0
        """

        fmt_kwargs: Dict[str, Any] = {}

        if background_color is not None:
            fmt_kwargs["background_color_style"] = ColorStyle.auto(
                background_color
            )
        if text_align is not None:
            fmt_kwargs["horizontal_alignment"] = text_align
        if vertical_align is not None:
            fmt_kwargs["vertical_alignment"] = vertical_align
        if wrap is not None:
            fmt_kwargs["wrap_strategy"] = wrap

        foreground_color_style = None
        if text_color is not None:
            foreground_color_style = ColorStyle.auto(text_color)
        fmt_kwargs["text_format"] = TextFormat(
            foreground_color_style=foreground_color_style,
            font_family=font_family,
            font_size=font_size,
            bold=bold,
            italic=italic,
            strikethrough=strikethrough,
            underline=underline,
        )

        if len(fmt_kwargs) > 0:
            cell_data = CellData(user_entered_format=CellFormat(**fmt_kwargs))
            self._pending_requests.append(
                cell_data.updateRequest(self._get_grid_range(range_a1))
            )

        if update:
            self.update()

    def format_number_cell(
        self,
        range_a1: str,
        fmt_type: NumberFormatType,
        pattern: str,
        *,
        update: bool = False,
    ):
        """Formats the given number cell(s).

        Args:
            range_a1 (|str|): The cell range.
            fmt_type (|NumberFormatType|): The format type.
            pattern (|str|): The formatting pattern.
                See https://developers.google.com/sheets/api/guides/formats.
            update (|bool|): Whether to update the worksheet.

        .. versionadded:: 0.2.0
        """

        cell_data = CellData(
            user_entered_format=CellFormat(
                number_format=NumberFormat(
                    format_type=fmt_type, pattern=pattern
                )
            )
        )
        self._pending_requests.append(
            cell_data.updateRequest(self._get_grid_range(range_a1))
        )

        if update:
            self.update()
