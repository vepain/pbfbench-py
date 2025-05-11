"""Shell logics."""

from pathlib import Path

BASH_SHEBANG = "#!/bin/bash"


class Variable:
    """A shell variable."""

    def __init__(self, name: str) -> None:
        """Initialize."""
        self.__name = name

    def name(self) -> str:
        """Get name."""
        return self.__name

    def eval(self) -> str:
        """Get evaluated variable."""
        return f"${{{self.__name}}}"

    def set(self, value: str) -> str:
        """Set variable."""
        return f"{self.__name}={value}"


def path_to_str(path: Path | str) -> str:
    """Convert path to string."""
    return f'"{path}"'


def is_a_command(bash_line: str) -> bool:
    """Check if bash line is a command."""
    lstrip = bash_line.lstrip()
    return len(lstrip) > 0 and lstrip[0] != "#" and lstrip[-1] != "\\"


def manage_error_and_exit(bash_line: str, exit_cmd: str) -> str:
    """Return new command executing an exit cmd if the first one exited with error."""
    if is_a_command(bash_line):
        return bash_line + " || " + exit_cmd
    return bash_line


def exit_on_error(bash_line: str) -> str:
    """Return new command that exits the script if the command fails."""
    if is_a_command(bash_line):
        return manage_error_and_exit(bash_line, "exit 1")
    return bash_line


if __name__ == "__main__":
    from rich.markdown import Markdown as Md

    from pbfbench import root_logging

    v = Variable("foo")
    p = Path("tmp/there is a space/file.txt")
    sh_lines = "\n".join(
        [v.set(path_to_str(p)), f"echo {v.eval()}"],
    )
    root_logging.CONSOLE.print(Md(f"```bash\n{sh_lines}\n```"))
