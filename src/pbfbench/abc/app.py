"""ABC for apps."""

from enum import StrEnum

import pbfbench.abc.tool.description as abc_tool_desc


class FinalCommands(StrEnum):
    """Final commands."""

    INIT = "init"
    CHECK = "check"
    RUN = "run"

    def help(self, tool_description: abc_tool_desc.Description) -> str:
        """Get help string."""
        return " ".join(
            [
                "pbfbench",
                tool_description.topic().cmd(),
                tool_description.cmd(),
                "run",
                "--help",
            ],
        )
