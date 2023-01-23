"""
The `codepost_powertools` package on the command line.
"""

# =============================================================================

import click
import cloup

from codepost_powertools import grading, rubric
from codepost_powertools.info import __version__, package_name

# =============================================================================

_cli_name = "cptools"

# =============================================================================


@cloup.group(
    _cli_name,
    sections=[
        # pylint: disable=protected-access
        # Access the `_cli_group.group` group of each submodule
        group._cli_group.group.as_section()
        for group in (
            grading,
            rubric,
        )
    ],
    help=__doc__,
)
@click.version_option(
    version=__version__,
    package_name=package_name,
    prog_name=_cli_name,
    message="%(prog)s (%(package)s), version %(version)s",
)
def cli():
    pass


# =============================================================================

if __name__ == "__main__":
    cli()
