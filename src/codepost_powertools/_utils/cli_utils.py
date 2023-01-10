"""
Utilities for the command-line interface.
"""

# =============================================================================

import functools
import itertools
import sys
import time
from typing import List

import click

from codepost_powertools._utils._logger import _get_logger
from codepost_powertools._utils.file_io import validate_csv_silent
from codepost_powertools.config import log_in_codepost

# =============================================================================

# If running on command line, `log` is always True
logger = _get_logger(log=True)

# =============================================================================


class NaturalOrderGroup(click.Group):
    """A group that lists commands in the given order.

    .. versionadded:: 0.1.0
    """

    def list_commands(self, ctx: click.Context) -> List[str]:
        return list(self.commands.keys())


class NaturalOrderCollection(click.CommandCollection):
    """A command collection that lists commands in the given groups
    order.

    .. versionadded:: 0.1.0
    """

    def list_commands(self, ctx: click.Context) -> List[str]:
        # flatten the commands from each source
        return list(
            itertools.chain.from_iterable(
                multi_command.list_commands(ctx)
                for multi_command in self.sources
            )
        )

    def list_command_objs(self) -> List[click.Command]:
        """Returns a list of all the command objects, as opposed to only
        the command names, as ``list_commands()`` does.

        .. versionadded:: 0.1.0
        """
        return list(
            itertools.chain.from_iterable(
                multi_command.commands.values()
                for multi_command in self.sources
            )
        )


def get_help_str(command_title: str, command: click.Command) -> str:
    """Returns the help string of the given command.

    .. versionadded:: 0.1.0
    """
    # Reference: https://stackoverflow.com/a/43178373
    with click.Context(command, info_name=command_title) as ctx:
        return command.get_help(ctx)


# =============================================================================


def _format_time(elapsed: float) -> str:
    """Formats the given number of seconds into a readable time str.

    .. versionadded:: 0.1.0
    """

    if elapsed < 60:
        return f"{elapsed:.2f} sec"
    minutes, seconds = divmod(elapsed, 60)
    if minutes < 60:
        return f"{minutes:.0f} min, {seconds:.2f} sec"
    hours, minutes = divmod(minutes, 60)
    return f"{hours:.0f} hr, {minutes:.0f} min, {seconds:.2f} sec"


def log_start_end(func):
    """Decorates a `click` command to log the start and end.

    Also logs in to codePost before calling the function, and logs any
    uncaught exceptions during execution.

    .. versionadded:: 0.1.0
    """

    @functools.wraps(func)
    @click.pass_context
    def log(ctx, **kwargs):
        logger.trace("Start")
        start = time.time()

        had_error = False

        def onerror(exception):
            nonlocal had_error
            had_error = True

        success = log_in_codepost(log=True)
        if not success:
            had_error = True
        else:
            with logger.catch(
                reraise=False, onerror=onerror, message="Uncaught exception"
            ):
                # unfortunately can't exit with nonzero status code if
                # handled errors occur, since there's no way to know
                # from this outer scope
                # also pass `log=True`
                ctx.invoke(func, **kwargs, log=True)

        end = time.time()
        logger.trace("Done")

        logger.trace("Total time: {}", _format_time(end - start))

        if had_error:
            sys.exit(1)

    return log


# =============================================================================


def convert_course(func):
    """Decorates a `click` command to convert the two arguments
    `course_name` and `course_period` into a CourseArg tuple.

    .. versionadded:: 0.1.0
    """

    @functools.wraps(func)
    def wrapped(course_name, course_period, **kwargs):
        return func(course=(course_name, course_period), **kwargs)

    return wrapped


# =============================================================================


def cb_validate_csv(ctx, param, value):
    """A callback to validate that the given filepath has a ".csv"
    extension.

    .. versionadded:: 0.1.0
    """
    success, error_msg = validate_csv_silent(value)
    if not success:
        raise click.BadParameter(error_msg)
    return value
