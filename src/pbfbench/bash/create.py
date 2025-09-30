"""Bash script creation module."""

from collections.abc import Iterable
from pathlib import Path

import pbfbench.bash.items as bash_items


def create(bash_lines: Iterable[str], script_path: Path) -> None:
    """Create a bash script.

    The bash lines should not contain a newline at the end.
    """
    with script_path.open("w") as f_out:
        f_out.write(bash_items.BASH_SHEBANG + "\n")
        f_out.write("\n")
        for line in bash_lines:
            f_out.write(line + "\n")
