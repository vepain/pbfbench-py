"""ABC for apps."""

from enum import StrEnum


class FinalCommands(StrEnum):
    """Final commands."""

    # FIXME the structure of command interface will change

    INIT = "init"
    CHECK = "check"
    RUN = "run"
