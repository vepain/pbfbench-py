"""ABC for apps."""

from enum import StrEnum


class FinalCommands(StrEnum):
    """Final commands."""

    INIT = "init"
    CHECK = "check"
    RUN = "run"
