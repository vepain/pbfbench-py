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


def path_to_str(path: Path) -> str:
    """Convert path to string."""
    return f'"{path}"'


if __name__ == "__main__":
    from rich.markdown import Markdown as Md

    from pbfbench import root_logging

    v = Variable("foo")
    p = Path("tmp/there is a space/file.txt")
    sh_lines = "\n".join(
        [v.set(path_to_str(p)), f"echo {v.eval()}"],
    )
    root_logging.CONSOLE.print(Md(f"```bash\n{sh_lines}\n```"))
