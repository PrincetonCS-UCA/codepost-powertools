"""
Automatically generates ``cptools`` cli help docs.
"""

import textwrap
from pathlib import Path


def generate_cli_docs():
    try:
        # pylint: disable=import-outside-toplevel
        from codepost_powertools.__main__ import cli
        from codepost_powertools._utils.cli_utils import get_help_str
    except ImportError:
        return "Sorry, could not generate CLI help text."

    help_file_lines = [
        "*This page was automatically generated when building the docs.*",
        "",
    ]

    def add_command_help(name, command):
        lines = []
        # add the header
        title = f"``{name}`` command"
        lines.append(title)
        lines.append("-" * len(title))
        lines.append("")
        # add the help string
        lines.append(".. code-block:: text")
        lines.append("")
        help_str = get_help_str(name, command)
        # prefix each line with 3 spaces
        lines.append(textwrap.indent(help_str, " " * 3))
        lines.append("")
        help_file_lines.extend(lines)

    # add the top level command
    add_command_help(cli.name, cli)
    # add all commands
    for cmd in cli.list_command_objs():
        add_command_help(f"{cli.name} {cmd.name}", cmd)

    return "\n".join(help_file_lines)


def generate():
    CLI_HELP_DIR = Path("cli")
    CLI_HELP_DIR.mkdir(parents=True, exist_ok=True)
    help_file = CLI_HELP_DIR / "cptools-cli-help-generated.rst"
    help_file.write_text(generate_cli_docs(), encoding="utf-8")
