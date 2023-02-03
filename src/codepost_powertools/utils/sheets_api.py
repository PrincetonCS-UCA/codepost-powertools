"""
Contains helpers for communicating with the Google Sheets API.
"""
# pylint: disable=too-many-lines

# Spreadsheet batch updating:
# https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/batchUpdate
# https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/request

# =============================================================================

from __future__ import annotations

from enum import Enum, auto
from typing import Any, Dict, Iterable, List, Optional, Type, Union, overload

from gspread.utils import a1_range_to_grid_range as gridrange

# =============================================================================


class NameValueEnum(Enum):
    """An enum parent class that sets all the values to the name of the
    variable.

    :meta docskip:
    """

    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name


# =============================================================================

# regular JSON, but don't include None
JSON = Union[bool, int, float, str, List["JSON"], Dict[str, "JSON"]]


class ToJson:
    """A parent class that can be converted into a JSON value.

    When the ``json()`` method is called, a defensive copy will be
    returned to preserve immutability of the object.

    Constructor kwargs:
        json (JSON): The JSON representation value.
        filter_none (bool): Whether to filter ``None`` values out of the
            top-level values of the dict.

    :meta docskip:
    """

    def __init__(self, *, json, filter_none: bool = True, **kwargs):
        if json is None:
            raise TypeError("ToJson.__init__() missing `json` kwarg")
        if filter_none and isinstance(json, dict):
            json = {
                key: value for key, value in json.items() if value is not None
            }
        self._json = json
        super().__init__(**kwargs)

    def _to_json(self, value):
        if isinstance(value, (bool, int, float, str)):
            # already immutable
            return value
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, list):
            return [self._to_json(val) for val in value]
        if isinstance(value, dict):
            values = {}
            for key, val in value.items():
                val_json = self._to_json(val)
                if isinstance(val_json, dict) and len(val_json) == 0:
                    # empty dict; don't include
                    continue
                values[key] = val_json
            return values
        if isinstance(value, ToJson):
            return value.json()
        raise TypeError(
            f"cannot serialize type {value.__class__.__name__} to JSON"
        )

    def json(self) -> JSON:
        return self._to_json(self._json)  # pylint: disable=no-member


# =============================================================================


class HasFields:
    """A parent class that indicates that a subclass has a ``fields()``
    method that returns its set fields.

    If ``fields`` is not given and the subclass also inherits from
    ``ToJson``, the keys of the JSON representation will be used as the
    fields.

    Constructor args:
        fields (Iterable[str]): The fields to use.
        exclude_fields (Iterable[str]): Fields to exclude.
            Only has effect if ``fields`` is not given.

    :meta docskip:
    """

    def __init__(
        self,
        *,
        fields: Optional[Iterable[str]] = None,
        exclude_fields: Optional[Iterable[str]] = None,
        **kwargs,
    ):
        if fields is not None:
            pass
        elif isinstance(self, ToJson) and isinstance(
            getattr(self, "_json", None), dict
        ):
            if exclude_fields is None:
                exclude_fields = set()
            else:
                exclude_fields = set(exclude_fields)
            # return the keys of the json dict
            fields = []
            for key, value in self._json.items():
                if key in exclude_fields:
                    continue
                # if isinstance(value, (bool, int, float, str, list, dict)):
                #     fields.append(key)
                #     continue
                if isinstance(value, HasFields):
                    fields.extend(
                        [f"{key}.{field}" for field in value.fields()]
                    )
                    continue
                # fallback: just use the key itself
                fields.append(key)
                # raise TypeError(
                #     "cannot extract fields from type "
                #     f"{value.__class__.__name__}"
                # )
        else:
            raise TypeError("HasFields.__init__() missing `fields` kwarg")
        self._fields = list(fields)
        super().__init__(**kwargs)

    def fields(self) -> List[str]:
        return self._fields


class UnionField(ToJson):
    """A parent class that indicates that a subclass can only have one
    of multiple options.

    :meta docskip:
    """

    __INIT_KEY = object()

    def __init__(self, __key, field, value, **kwargs):
        """DO NOT CALL THIS CONSTRUCTOR"""
        if __key is not UnionField.__INIT_KEY:
            raise RuntimeError("Do not call this constructor directly")
        super().__init__(json={field: value}, filter_none=False, **kwargs)


# =============================================================================


class Dimension(NameValueEnum):
    """Indicates which dimension an operation should apply to.

    https://developers.google.com/sheets/api/reference/rest/v4/Dimension
    """

    ROWS = auto()
    """Operates on the rows of a sheet."""
    COLUMNS = auto()
    """Operates on the columns of a sheet."""


class DimensionRange(ToJson):
    """A range along a single dimension on a sheet.

    All indexes are zero-based. Indexes are half open: the start index
    is inclusive and the end index is exclusive. Missing indexes
    indicate the range is unbounded on that side.

    https://developers.google.com/sheets/api/reference/rest/v4/DimensionRange
    """

    def __init__(
        self,
        *,
        sheet_id: int,
        dimension: Dimension,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
    ):
        super().__init__(
            json={
                "sheetId": sheet_id,
                "dimension": dimension,
                "startIndex": start_index,
                "endIndex": end_index,
            }
        )

    @classmethod
    def from_range(cls, *, sheet_id: int, dimension: Dimension, range_a1: str):
        if dimension == Dimension.ROWS:
            dim = "Row"
        elif dimension == Dimension.COLUMNS:
            dim = "Column"
        grid = gridrange(range_a1)
        return cls(
            sheet_id=sheet_id,
            dimension=dimension,
            start_index=grid.get(f"start{dim}Index"),
            end_index=grid.get(f"end{dim}Index"),
        )

    @classmethod
    def rows(cls, *, sheet_id: int, range_a1: str):
        return cls.from_range(
            sheet_id=sheet_id, dimension=Dimension.ROWS, range_a1=range_a1
        )

    @classmethod
    def cols(cls, *, sheet_id: int, range_a1: str):
        return cls.from_range(
            sheet_id=sheet_id, dimension=Dimension.COLUMNS, range_a1=range_a1
        )


# =============================================================================

# Sheets


class GridProperties(ToJson, HasFields):
    """Properties of a grid.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/sheets#GridProperties
    """

    def __init__(
        self,
        *,
        row_count: Optional[int] = None,
        col_count: Optional[int] = None,
        frozen_row_count: Optional[int] = None,
        frozen_col_count: Optional[int] = None,
        hide_gridlines: Optional[bool] = None,
        row_group_control_after: Optional[bool] = None,
        col_group_control_after: Optional[bool] = None,
    ):
        super().__init__(
            json={
                "rowCount": row_count,
                "columnCount": col_count,
                "frozenRowCount": frozen_row_count,
                "frozenColumnCount": frozen_col_count,
                "hideGridlines": hide_gridlines,
                "rowGroupControlAfter": row_group_control_after,
                "columnGroupControlAfter": col_group_control_after,
            }
        )


class SheetProperties(ToJson, HasFields):
    """Properties of a sheet.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/sheets#sheetproperties
    """

    def __init__(
        self,
        *,
        sheet_id: int,
        title: Optional[str] = None,
        index: Optional[int] = None,
        grid_properties: Optional[GridProperties] = None,
        hidden: Optional[bool] = None,
        tab_color_style: Optional[ColorStyle] = None,
        right_to_left: Optional[bool] = None,
    ):
        super().__init__(
            json={
                "sheetId": sheet_id,
                "title": title,
                "index": index,
                "gridProperties": grid_properties,
                "hidden": hidden,
                "tabColorStyle": tab_color_style,
                "rightToLeft": right_to_left,
            },
            exclude_fields={"sheetId"},
        )

    def updateRequest(self) -> Dict:
        """Returns the ``UpdateSheetPropertiesRequest`` dict with these
        properties.

        https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/request#updatesheetpropertiesrequest
        """
        return {
            "updateSheetProperties": {
                "properties": self.json(),
                "fields": ",".join(self.fields()),
            }
        }


class DimensionProperties(ToJson, HasFields):
    """Properties about a dimension.

    .. note::
       Excludes the field ``"developerMetadata"``.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/sheets#DimensionProperties
    """

    def __init__(
        self,
        *,
        hidden_by_user: Optional[bool] = None,
        pixel_size: Optional[int] = None,
        developer_metadata=None,
    ):
        if developer_metadata is not None:
            raise NotImplementedError("`developer_metadata` field")
        super().__init__(
            json={
                "hiddenByUser": hidden_by_user,
                "pixelSize": pixel_size,
            }
        )

    def updateRequest(self, dim_range: DimensionRange) -> Dict:
        """Returns the ``UpdateDimensionPropertiesRequest`` dict with
        these properties and the given dimension range.

        .. note::
           Excludes the union field ``"dataSourceSheetRange"``.

        https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/request#updatedimensionpropertiesrequest
        """
        return {
            "updateDimensionProperties": {
                "properties": self.json(),
                "fields": ",".join(self.fields()),
                "range": dim_range.json(),
            }
        }


class ConditionalFormatRule:
    """A rule describing a conditional format.

    .. warning::
       This class is not implemented at all.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/sheets#conditionalformatrule
    """


# =============================================================================

# Cells


class CellData(ToJson, HasFields):
    """Data about a specific cell.

    .. note::
       Excludes the fields ``"textFormatRuns[]"``, ``"pivotTable"``,
       ``"dataSourceTable"``, and ``"dataSourceFormula"``.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#CellData
    """

    def __init__(
        self,
        *,
        user_entered_value: Optional[ExtendedValue] = None,
        user_entered_format: Optional[CellFormat] = None,
        hyperlink: Optional[str] = None,
        note: Optional[str] = None,
        text_format_runs=None,
        data_validation: Optional[DataValidationRule] = None,
        pivot_table=None,
        data_source_table=None,
        data_source_formula=None,
    ):
        if text_format_runs is not None:
            raise NotImplementedError("`text_format_runs` field")
        if pivot_table is not None:
            raise NotImplementedError("`pivot_table` field")
        if data_source_table is not None:
            raise NotImplementedError("`data_source_table` field")
        if data_source_formula is not None:
            raise NotImplementedError("`data_source_formula` field")
        super().__init__(
            json={
                "userEnteredValue": user_entered_value,
                "userEnteredFormat": user_entered_format,
                "hyperlink": hyperlink,
                "note": note,
                "dataValidation": data_validation,
            }
        )

    def updateRequest(self, grid_range: GridRange) -> Dict:
        """Returns the ``RepeatCellRequest`` dict with these properties
        and the given grid range.

        https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/request#repeatcellrequest
        """
        return {
            "repeatCell": {
                "range": grid_range.json(),
                "cell": self.json(),
                "fields": ",".join(self.fields()),
            }
        }


class CellFormat(ToJson, HasFields):
    """The format of a cell.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#CellFormat
    """

    def __init__(
        self,
        *,
        number_format: Optional[NumberFormat] = None,
        background_color_style: Optional[ColorStyle] = None,
        borders: Optional[Borders] = None,
        padding: Optional[Padding] = None,
        horizontal_alignment: Optional[HorizontalAlign] = None,
        vertical_alignment: Optional[VerticalAlign] = None,
        wrap_strategy: Optional[WrapStrategy] = None,
        text_direction: Optional[TextDirection] = None,
        text_format: Optional[TextFormat] = None,
        hyperlink_display_type: Optional[HyperlinkDisplayType] = None,
        text_rotation: Optional[TextRotation] = None,
    ):
        super().__init__(
            json={
                "numberFormat": number_format,
                "backgroundColorStyle": background_color_style,
                "borders": borders,
                "padding": padding,
                "horizontalAlignment": horizontal_alignment,
                "verticalAlignment": vertical_alignment,
                "wrapStrategy": wrap_strategy,
                "textDirection": text_direction,
                "textFormat": text_format,
                "hyperlinkDisplayType": hyperlink_display_type,
                "textRotation": text_rotation,
            }
        )


class NumberFormat(ToJson):
    """The number format of a cell.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#NumberFormat
    """

    def __init__(
        self, *, format_type: NumberFormatType, pattern: Optional[str] = None
    ):
        super().__init__(
            json={
                "type": format_type,
                "pattern": pattern,
            }
        )


class NumberFormatType(NameValueEnum):
    """The number format of the cell.

    The examples are in the ``en_US`` locale, but the actual format
    depends on the locale of the spreadsheet.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#numberformattype
    """

    TEXT = auto()
    """Text formatting, e.g. ``1000.12``"""
    NUMBER = auto()
    """Number formatting, e.g. ``1,000.12``"""
    PERCENT = auto()
    """Percent formatting, e.g. ``10.12%``"""
    CURRENCY = auto()
    """Currency formatting, e.g. ``$1,000.12``"""
    DATE = auto()
    """Date formatting, e.g. ``9/26/2008``"""
    TIME = auto()
    """Time formatting, e.g. ``3:59:00 PM``"""
    DATE_TIME = auto()
    """Date+Time formatting, e.g. ``9/26/08 15:59:00``"""
    SCIENTIFIC = auto()
    """Scientific number formatting, e.g. ``1.01E+03``"""


class Borders(ToJson, HasFields):
    """The borders of the cell.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#Borders
    """

    def __init__(
        self,
        *,
        top: Optional[Border] = None,
        bottom: Optional[Border] = None,
        left: Optional[Border] = None,
        right: Optional[Border] = None,
    ):
        super().__init__(
            json={
                "top": top,
                "bottom": bottom,
                "left": left,
                "right": right,
            }
        )


class Border(ToJson, HasFields):
    """A border along a cell.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#border
    """

    def __init__(
        self,
        *,
        style: Optional[Style] = None,
        color_style: Optional[ColorStyle] = None,
    ):
        super().__init__(
            json={
                "style": style,
                "colorStyle": color_style,
            }
        )


class Style(NameValueEnum):
    """The style of a border.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#style
    """

    DOTTED = auto()
    """The border is dotted."""
    DASHED = auto()
    """The border is dashed."""
    SOLID = auto()
    """The border is a thin solid line."""
    SOLID_MEDIUM = auto()
    """The border is a medium solid line."""
    SOLID_THICK = auto()
    """The border is a thick solid line."""
    NONE = auto()
    """No border. Used only when updating a border in order to erase it."""
    DOUBLE = auto()
    """The border is two solid lines."""


class Padding(ToJson):
    """The amount of padding around the cell, in pixels.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#Padding
    """

    def __init__(self, *, top: int, right: int, bottom: int, left: int):
        super().__init__(
            json={
                "top": top,
                "right": right,
                "bottom": bottom,
                "left": left,
            },
            filter_none=False,
        )


class VerticalAlign(NameValueEnum):
    """The vertical alignment of text in a cell.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#VerticalAlign
    """

    TOP = auto()
    """The text is explicitly aligned to the top of the cell."""
    MIDDLE = auto()
    """The text is explicitly aligned to the middle of the cell."""
    BOTTOM = auto()
    """The text is explicitly aligned to the bottom of the cell."""


class WrapStrategy(NameValueEnum):
    """How to wrap text in a cell.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#WrapStrategy
    """

    OVERFLOW_CELL = auto()
    """Lines that are longer than the cell width will be written in the
    next cell over, so long as that cell is empty. If the next cell over
    is non-empty, this behaves the same as :attr:`~WrapStrategy.CLIP`.
    The text will never wrap to the next line unless the user manually
    inserts a new line.

    Example:

    .. code-block:: text

       | First sentence. |
       | Manual newline that is very long. <- Text continues into next cell
       | Next newline.   |
    """

    CLIP = auto()
    """Lines that are longer than the cell width will be clipped. The
    text will never wrap to the next line unless the user manually
    inserts a new line.

    Example:

    .. code-block:: text

       | First sentence. |
       | Manual newline t| <- Text is clipped
       | Next newline.   |
    """

    WRAP = auto()
    """Words that are longer than a line are wrapped at the character
    level rather than clipped.

    Example:

    .. code-block:: text

       | Cell has a |
       | loooooooooo| <- Word is broken.
       | ong word.  |
    """


class TextDirection(NameValueEnum):
    """The direction of text in a cell.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#TextDirection
    """

    LEFT_TO_RIGHT = auto()
    """Left to right."""
    RIGHT_TO_LEFT = auto()
    """Right to left."""


class HyperlinkDisplayType(NameValueEnum):
    """Whether to explicitly render a hyperlink.

    If not specified, the hyperlink is linked.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#HyperlinkDisplayType
    """

    LINKED = auto()
    """A hyperlink should be explicitly rendered."""
    PLAIN_TEXT = auto()
    """A hyperlink should not be rendered."""


class TextRotation(UnionField):
    """The rotation applied to text in a cell.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#textrotation
    """

    @classmethod
    def angle(cls, angle: int) -> TextRotation:
        """The angle between the standard orientation and the desired
        orientation, measured in degrees.

        Valid values are between -90 and 90. Positive angles are angled
        upwards, negative are angled downwards.

        .. note::
           For LTR text direction positive angles are in the
           counterclockwise direction, whereas for RTL they are in the
           clockwise direction.
        """
        if not -90 <= angle <= 90:
            raise ValueError("invalid angle: must be between [-90, 90]")
        return cls(getattr(cls, "_UnionField__INIT_KEY"), "angle", angle)

    @classmethod
    def vertical(cls, vertical: bool) -> TextRotation:
        """If true, text reads top to bottom, but the orientation of
        individual characters is unchanged.
        """
        return cls(getattr(cls, "_UnionField__INIT_KEY"), "vertical", vertical)


class DataValidationRule(ToJson, HasFields):
    """A data validation rule.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#DataValidationRule
    """

    def __init__(
        self,
        *,
        condition: BooleanCondition,
        input_message: Optional[str] = None,
        strict: Optional[bool] = None,
        show_custom_ui: Optional[bool] = None,
    ):
        if not condition.supports(self):
            raise ValueError(
                "given condition not supported for data validation"
            )
        super().__init__(
            json={
                "condition": condition,
                "inputMessage": input_message,
                "strict": strict,
                "showCustomUi": show_custom_ui,
            }
        )


# =============================================================================

# Other


class Color(ToJson):
    """A color in the RGB color space.

    .. note::
       Alpha values are not supported.
    """

    MAX_RGB = 255

    def __init__(self, red: float, green: float, blue: float):
        """Creates a color from 3 floats between [0, 1]."""
        values = {}
        for key, color_val in zip(
            ("red", "green", "blue"), (red, green, blue)
        ):
            if not 0 <= color_val <= 1:
                raise ValueError(f"{key} is not between [0, 1]")
            values[key] = color_val
        super().__init__(json=values, filter_none=False)

    @classmethod
    def ints(cls, red: int, green: int, blue: int) -> Color:
        """Creates a color from 3 integers between [0, 255]."""
        return cls(
            *(color_val / cls.MAX_RGB for color_val in (red, green, blue))
        )

    @classmethod
    def auto(cls, *args) -> Color:
        """Automatically constructs a color based on the given arg(s)."""
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, Color):
                # another color: return itself
                return arg
            if isinstance(arg, tuple):
                # pass it on to the tuple checker
                args = arg
        if len(args) == 3:
            # 3-tuple of colors
            r, g, b = args
            if all(isinstance(x, float) for x in args):
                # call will fail if invalid floats
                return cls(r, g, b)
            if all(isinstance(x, int) for x in args):
                # call with fail if invalid ints
                return cls.ints(r, g, b)
        raise TypeError(f"Could not create Color from: {args}")


class ColorStyle(UnionField):
    """A color value.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#ColorStyle
    """

    @classmethod
    def from_color(cls, color: Color) -> ColorStyle:
        return cls(getattr(cls, "_UnionField__INIT_KEY"), "rgbColor", color)

    @classmethod
    def rgb(cls, red: float, green: float, blue: float) -> ColorStyle:
        """Creates a color style from 3 floats between [0, 1]."""
        return cls(
            getattr(cls, "_UnionField__INIT_KEY"),
            "rgbColor",
            Color(red, green, blue),
        )

    @classmethod
    def rgb_ints(cls, red: int, green: int, blue: int) -> ColorStyle:
        """Creates a color style from 3 integers between [0, 255]."""
        return cls(
            getattr(cls, "_UnionField__INIT_KEY"),
            "rgbColor",
            Color.ints(red, green, blue),
        )

    @classmethod
    def theme(cls, theme_color_type: ThemeColorType) -> ColorStyle:
        return cls(
            getattr(cls, "_UnionField__INIT_KEY"),
            "themeColor",
            theme_color_type,
        )

    @classmethod
    def auto(cls, *args) -> ColorStyle:
        """Automatically constructs a color style based on the given
        arg(s).
        """
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, ThemeColorType):
                return cls.theme(arg)
        try:
            return cls.from_color(Color.auto(*args))
        except TypeError:
            raise TypeError(
                f"Could not create ColorStyle from: {args}"
            ) from None


class ThemeColorType(NameValueEnum):
    """Theme color types.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#ThemeColorType
    """

    TEXT = auto()
    """Represents the primary text color"""
    BACKGROUND = auto()
    """Represents the primary background color"""
    ACCENT1 = auto()
    """Represents the first accent color"""
    ACCENT2 = auto()
    """Represents the second accent color"""
    ACCENT3 = auto()
    """Represents the third accent color"""
    ACCENT4 = auto()
    """Represents the fourth accent color"""
    ACCENT5 = auto()
    """Represents the fifth accent color"""
    ACCENT6 = auto()
    """Represents the sixth accent color"""
    LINK = auto()
    """Represents the color to use for hyperlinks"""


class HorizontalAlign(NameValueEnum):
    """The horizontal alignment of text in a cell.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#HorizontalAlign
    """

    LEFT = auto()
    """The text is explicitly aligned to the left of the cell."""
    CENTER = auto()
    """The text is explicitly aligned to the center of the cell."""
    RIGHT = auto()
    """The text is explicitly aligned to the right of the cell."""


class TextFormat(ToJson, HasFields):
    """The format of a run of text in a cell.

    .. note::

       Since the ``Link`` type is simply ``{"uri": string}``, this class
       accepts the uri itself.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#TextFormat
    """

    def __init__(
        self,
        *,
        foreground_color_style: Optional[ColorStyle] = None,
        font_family: Optional[str] = None,
        font_size: Optional[int] = None,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        strikethrough: Optional[bool] = None,
        underline: Optional[bool] = None,
        link: Optional[str] = None,
    ):
        values = {
            "foregroundColorStyle": foreground_color_style,
            "fontFamily": font_family,
            "fontSize": font_size,
            "bold": bold,
            "italic": italic,
            "strikethrough": strikethrough,
            "underline": underline,
        }
        if link is not None:
            values["link"] = {"uri": link}  # type: ignore[assignment]
        super().__init__(json=values)


class ExtendedValue(UnionField):
    """The kinds of value that a cell in a spreadsheet can have.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#ExtendedValue
    """

    @classmethod
    def number(cls, number: Union[int, float]) -> ExtendedValue:
        return cls(
            getattr(cls, "_UnionField__INIT_KEY"), "numberValue", number
        )

    @classmethod
    def string(cls, string: str) -> ExtendedValue:
        return cls(
            getattr(cls, "_UnionField__INIT_KEY"), "stringValue", string
        )

    @classmethod
    def boolean(cls, boolean: bool) -> ExtendedValue:
        return cls(getattr(cls, "_UnionField__INIT_KEY"), "boolValue", boolean)

    @classmethod
    def formula(cls, formula: str) -> ExtendedValue:
        return cls(
            getattr(cls, "_UnionField__INIT_KEY"), "formulaValue", formula
        )


class BooleanCondition(ToJson):
    """A condition that can evaluate to true or false.

    This class is modified a bit from the official documentation, taking
    into consideration all the different condition types and value
    constraints.

    .. note::
       Excludes the condition types ``TEXT_NOT_EQ`` and ``DATE_NOT_EQ``,
       which are only supported by filters on data source objects.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#BooleanCondition
    """

    # pylint: disable=too-many-public-methods

    __INIT_KEY = object()

    def __init__(
        self,
        __key,
        type_,
        values: Optional[Iterable[Union[str, RelativeDate]]] = None,
        supports: Optional[Iterable[Type]] = None,
    ):
        """DO NOT CALL THIS CONSTRUCTOR

        :meta docskip:
        """
        if __key is not BooleanCondition.__INIT_KEY:
            raise RuntimeError("Do not call this constructor directly")
        json = {"type": type_}
        if values is not None:
            condition_values = []
            for value in values:
                if isinstance(value, RelativeDate):
                    key = "relativeDate"
                else:
                    key = "userEnteredValue"
                condition_values.append({key: value})
            json["values"] = condition_values
        super().__init__(json=json, filter_none=False)
        if supports is None:
            supports = (
                ConditionalFormatRule,
                DataValidationRule,
                FilterCriteria,
            )
        self._supports = tuple(supports)

    def supports(self, rule):
        """Checks if the given rule is supported by this
        BooleanCondition.

        It is up to the rules to determine if they are allowed to use
        this condition.

        Possible rules are:

        - :class:`ConditionalFormatRule`
        - :class:`DataValidationRule`
        - :class:`FilterCriteria`
        """
        if isinstance(rule, type):
            return rule in self._supports
        return isinstance(rule, self._supports)

    @classmethod
    def NUMBER_GREATER(cls, number: Union[int, float]) -> BooleanCondition:
        return cls(cls.__INIT_KEY, "NUMBER_GREATER", [str(number)])

    @classmethod
    def NUMBER_GREATER_THAN_EQ(
        cls, number: Union[int, float]
    ) -> BooleanCondition:
        return cls(cls.__INIT_KEY, "NUMBER_GREATER_THAN_EQ", [str(number)])

    @classmethod
    def NUMBER_LESS(cls, number: Union[int, float]) -> BooleanCondition:
        return cls(cls.__INIT_KEY, "NUMBER_LESS", [str(number)])

    @classmethod
    def NUMBER_LESS_THAN_EQ(
        cls, number: Union[int, float]
    ) -> BooleanCondition:
        return cls(cls.__INIT_KEY, "NUMBER_LESS_THAN_EQ", [str(number)])

    @classmethod
    def NUMBER_EQ(cls, number: Union[int, float]) -> BooleanCondition:
        # Note: does not support multiple ``ConditionValue``s for data
        # source objects
        return cls(cls.__INIT_KEY, "NUMBER_EQ", [str(number)])

    @classmethod
    def NUMBER_NOT_EQ(cls, number: Union[int, float]) -> BooleanCondition:
        # Note: does not support multiple ``ConditionValue``s for data
        # source objects
        return cls(cls.__INIT_KEY, "NUMBER_NOT_EQ", [str(number)])

    @classmethod
    def NUMBER_BETWEEN(
        cls, low: Union[int, float], high: Union[int, float]
    ) -> BooleanCondition:
        return cls(cls.__INIT_KEY, "NUMBER_BETWEEN", [str(low), str(high)])

    @classmethod
    def NUMBER_NOT_BETWEEN(
        cls, low: Union[int, float], high: Union[int, float]
    ) -> BooleanCondition:
        return cls(cls.__INIT_KEY, "NUMBER_NOT_BETWEEN", [str(low), str(high)])

    @classmethod
    def TEXT_CONTAINS(cls, value: str) -> BooleanCondition:
        return cls(cls.__INIT_KEY, "TEXT_CONTAINS", [value])

    @classmethod
    def TEXT_NOT_CONTAINS(cls, value: str) -> BooleanCondition:
        return cls(cls.__INIT_KEY, "TEXT_NOT_CONTAINS", [value])

    @classmethod
    def TEXT_STARTS_WITH(cls, value: str) -> BooleanCondition:
        return cls(
            cls.__INIT_KEY,
            "TEXT_STARTS_WITH",
            [value],
            supports=[ConditionalFormatRule, FilterCriteria],
        )

    @classmethod
    def TEXT_ENDS_WITH(cls, value: str) -> BooleanCondition:
        return cls(
            cls.__INIT_KEY,
            "TEXT_ENDS_WITH",
            [value],
            supports=[ConditionalFormatRule, FilterCriteria],
        )

    @classmethod
    def TEXT_EQ(cls, value: str) -> BooleanCondition:
        # Note: does not support multiple ``ConditionValue``s for data
        # source objects
        return cls(cls.__INIT_KEY, "TEXT_EQ", [value])

    @classmethod
    def TEXT_IS_EMAIL(cls) -> BooleanCondition:
        return cls(
            cls.__INIT_KEY, "TEXT_IS_EMAIL", supports=[DataValidationRule]
        )

    @classmethod
    def TEXT_IS_URL(cls) -> BooleanCondition:
        return cls(
            cls.__INIT_KEY, "TEXT_IS_URL", supports=[DataValidationRule]
        )

    @classmethod
    def DATE_EQ(cls, date: str) -> BooleanCondition:
        # Note: does not support multiple ``ConditionValue``s for data
        # source objects
        return cls(cls.__INIT_KEY, "DATE_EQ", [date])

    @classmethod
    def DATE_BEFORE(cls, date: Union[str, RelativeDate]) -> BooleanCondition:
        return cls(cls.__INIT_KEY, "DATE_BEFORE", [date])

    @classmethod
    def DATE_AFTER(cls, date: Union[str, RelativeDate]) -> BooleanCondition:
        return cls(cls.__INIT_KEY, "DATE_AFTER", [date])

    @classmethod
    def DATE_ON_OR_BEFORE(
        cls, date: Union[str, RelativeDate]
    ) -> BooleanCondition:
        return cls(
            cls.__INIT_KEY,
            "DATE_ON_OR_BEFORE",
            [date],
            supports=[DataValidationRule],
        )

    @classmethod
    def DATE_ON_OR_AFTER(
        cls, date: Union[str, RelativeDate]
    ) -> BooleanCondition:
        return cls(
            cls.__INIT_KEY,
            "DATE_ON_OR_AFTER",
            [date],
            supports=[DataValidationRule],
        )

    @classmethod
    def DATE_BETWEEN(cls, date1: str, date2: str) -> BooleanCondition:
        return cls(
            cls.__INIT_KEY,
            "DATE_BETWEEN",
            [date1, date2],
            supports=[DataValidationRule],
        )

    @classmethod
    def DATE_NOT_BETWEEN(cls, date1: str, date2: str) -> BooleanCondition:
        return cls(
            cls.__INIT_KEY,
            "DATE_NOT_BETWEEN",
            [date1, date2],
            supports=[DataValidationRule],
        )

    @classmethod
    def DATE_IS_VALID(cls) -> BooleanCondition:
        return cls(
            cls.__INIT_KEY, "DATE_IS_VALID", supports=[DataValidationRule]
        )

    @classmethod
    def ONE_OF_RANGE(cls, range_a1: str) -> BooleanCondition:
        # TODO: could validate that ``range_a1`` is a valid range in A1
        return cls(
            cls.__INIT_KEY,
            "ONE_OF_RANGE",
            [range_a1],
            supports=[DataValidationRule],
        )

    @classmethod
    def ONE_OF_LIST(cls, values: Iterable[str]) -> BooleanCondition:
        """The cell's value must be in the list of condition values.

        Supports any number of condition values, one per item in the
        list. Formulas are not supported in the values.
        """
        return cls(
            cls.__INIT_KEY,
            "ONE_OF_LIST",
            values,
            supports=[DataValidationRule],
        )

    @classmethod
    def BLANK(cls) -> BooleanCondition:
        return cls(
            cls.__INIT_KEY,
            "BLANK",
            supports=[ConditionalFormatRule, FilterCriteria],
        )

    @classmethod
    def NOT_BLANK(cls) -> BooleanCondition:
        return cls(
            cls.__INIT_KEY,
            "NOT_BLANK",
            supports=[ConditionalFormatRule, FilterCriteria],
        )

    @classmethod
    def CUSTOM_FORMULA(cls, formula: str) -> BooleanCondition:
        return cls(cls.__INIT_KEY, "CUSTOM_FORMULA", [formula])

    @overload
    @classmethod
    def BOOLEAN(cls) -> BooleanCondition:
        """Renders a cell checkbox, where TRUE renders as checked and
        FALSE renders as unchecked.
        """

    @overload
    @classmethod
    def BOOLEAN(cls, checked_value: Any) -> BooleanCondition:
        """Renders a cell checkbox, where the given value renders as
        checked and blank renders as unchecked.
        """

    @overload
    @classmethod
    def BOOLEAN(
        cls, checked_value: Any, unchecked_value: Any
    ) -> BooleanCondition:
        """Renders a cell checkbox, with the given values rendering as
        checked and unchecked, respectively.
        """

    @classmethod
    def BOOLEAN(cls, checked_value=None, unchecked_value=None):
        """Renders a cell checkbox, with the given values rendering as
        checked and unchecked, respectively.
        """
        values = []
        if checked_value is not None:
            values.append(checked_value)
            if unchecked_value is not None:
                values.append(unchecked_value)
        elif unchecked_value is not None:
            raise TypeError(
                "unchecked value given, but checked value not given"
            )
        return cls(
            cls.__INIT_KEY, "BOOLEAN", values, supports=[DataValidationRule]
        )

    # Helpful alias
    CHECKBOX = BOOLEAN


class RelativeDate(NameValueEnum):
    """Controls how a date condition is evaluated.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#RelativeDate
    """

    PAST_YEAR = auto()
    """The value is one year before today."""
    PAST_MONTH = auto()
    """The value is one month before today."""
    PAST_WEEK = auto()
    """The value is one week before today."""
    YESTERDAY = auto()
    """The value is yesterday."""
    TODAY = auto()
    """The value is today."""
    TOMORROW = auto()
    """The value is tomorrow."""


class MergeType(NameValueEnum):
    """The type of merge to create.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/request#mergetype
    """

    MERGE_ALL = auto()
    """Create a single merge from the range"""
    MERGE_COLUMNS = auto()
    """Create a merge for each column in the range"""
    MERGE_ROWS = auto()
    """Create a merge for each row in the range"""


class GridRange(ToJson):
    """A range on a sheet.

    All indexes are zero-based. Indexes are half open, i.e. the start
    index is inclusive and the end index is exclusive. Missing indexes
    indicate the range is unbounded on that side.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#GridRange
    """

    def __init__(
        self,
        *,
        sheet_id: int,
        start_row_index: Optional[int] = None,
        end_row_index: Optional[int] = None,
        start_col_index: Optional[int] = None,
        end_col_index: Optional[int] = None,
    ):
        for dim, start, end in (
            ("row", start_row_index, end_row_index),
            ("column", start_col_index, end_col_index),
        ):
            if start is None or end is None:
                continue
            if not start <= end:
                raise ValueError(
                    "start index must be less than or equal to end index "
                    f"({dim})"
                )
        super().__init__(
            json={
                "sheetId": sheet_id,
                "startRowIndex": start_row_index,
                "endRowIndex": end_row_index,
                "startColumnIndex": start_col_index,
                "endColumnIndex": end_col_index,
            }
        )

    @classmethod
    def entire_sheet(cls, *, sheet_id: int):
        return cls(sheet_id=sheet_id)

    @classmethod
    def from_range(cls, *, sheet_id: int, range_a1: str):
        grid_range = cls(sheet_id=sheet_id)
        for key, value in gridrange(range_a1).items():
            grid_range._json[key] = value
        return grid_range

    def mergeRequest(
        self, *, merge_type: MergeType = MergeType.MERGE_ALL
    ) -> Dict:
        """Returns the ``MergeCellsRequest`` dict for this GridRange.

        https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/request#MergeCellsRequest
        """
        return {
            "mergeCells": {
                "range": self.json(),
                "mergeType": merge_type.value,
            }
        }


class FilterCriteria:
    """Criteria for showing/hiding rows in a filter or filter view.

    .. warning::
       This class is not implemented at all.

    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#FilterCriteria
    """
