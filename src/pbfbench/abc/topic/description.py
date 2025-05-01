"""Topics abstract module."""

from __future__ import annotations


class Description:
    """Topic description."""

    def __init__(self, name: str, cmd: str) -> None:
        self.__name = name
        self.__cmd = cmd

    def name(self) -> str:
        """Get name."""
        return self.__name

    def cmd(self) -> str:
        """Get command."""
        return self.__cmd
