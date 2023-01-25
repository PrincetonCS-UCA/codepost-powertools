"""
Private utilities.

.. warning::
   Utilities in this subpackage do not need to maintain backward
   compatibility with previous versions, as they are private utilities
   meant to be used as internal helpers. Therefore, behavior of these
   functions may change, even between minor or patch versions.
"""

# =============================================================================

from typing import Optional

from codepost_powertools._utils._logger import _get_logger
from codepost_powertools._utils.handle_errors import handle_error

# =============================================================================

__all__ = (
    "handle_error",
    "pluralize",
    "with_pluralized",
)

# =============================================================================


def pluralize(count: int, word: str, *, plural: Optional[str] = None) -> str:
    """Returns the pluralized version of the given word, depending on
    the count.

    If ``plural`` is given, it is used as the plural word. Otherwise, an
    ``"s"`` is appended to the given word.

    Args:
       count (|int|): The number of items.
       word (|str|): The singular version of the word.
       plural (|str|): The plural version of the word to use.

    Returns:
        |str|: The pluralized word.

    .. versionadded:: 0.2.0
    """
    if count == 1:
        return word
    if plural is not None:
        return plural
    return f"{word}s"


def with_pluralized(
    count: int, word: str, *, plural: Optional[str] = None
) -> str:
    """Returns the count and the pluralized version of the given word,
    depending on the count.

    If ``plural`` is given, it is used as the plural word. Otherwise, an
    ``"s"`` is appended to the given word.

    Args:
       count (|int|): The number of items.
       word (|str|): The singular version of the word.
       plural (|str|): The plural version of the word to use.

    Returns:
        |str|: The count and the pluralized word, with a space between.

    .. versionadded:: 0.2.0
    """
    return f"{count} {pluralize(count, word, plural=plural)}"
