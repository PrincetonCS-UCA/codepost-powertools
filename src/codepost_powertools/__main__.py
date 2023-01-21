"""
The `codepost_powertools` package on the command line.
"""

# =============================================================================

import click

from codepost_powertools import grading, rubric
from codepost_powertools._utils.cli_utils import NaturalOrderCollection
from codepost_powertools.info import __version__, package_name

# =============================================================================

_cli_name = "cptools"

# =============================================================================

cli = NaturalOrderCollection(
    name=_cli_name,
    sources=[
        # pylint: disable=protected-access
        # Access the `_cli_group.group` group of each submodule
        group._cli_group.group
        for group in (
            grading,
            rubric,
        )
    ],
    help=__doc__,
)

cli = click.version_option(
    version=__version__,
    package_name=package_name,
    prog_name=_cli_name,
    message="%(prog)s (%(package)s), version %(version)s",
)(cli)

# =============================================================================

if __name__ == "__main__":
    cli()
