"""
The `codepost_powertools` package on the command line.
"""

# =============================================================================

import click

from codepost_powertools import __version__, grading
from codepost_powertools._utils.cli_utils import NaturalOrderCollection

# =============================================================================

__cli_name__ = "cptools"

# =============================================================================

# pylint: disable=protected-access
# Access the `_cli_group.group` group of each submodule
cmd_collection = NaturalOrderCollection(
    name=__cli_name__,
    sources=[group._cli_group.group for group in (grading,)],
    help=__doc__,
)


@click.version_option(
    version=__version__,
    package_name=__package__ or "codepost_powertools",
    prog_name=__cli_name__,
    message="%(prog)s (%(package)s), version %(version)s",
)
def cli():
    cmd_collection()


# =============================================================================

if __name__ == "__main__":
    cli()
