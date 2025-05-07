"""Topic visitor abstract module."""

from __future__ import annotations

import logging
from abc import abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    import pbfbench.abc.tool.description as abc_tool_desc
    import pbfbench.abc.topic.description as abc_topic_desc

_LOGGER = logging.getLogger(__name__)


class Topics(StrEnum):
    """Topics."""

    @classmethod
    def from_description(
        cls,
        topic_description: abc_topic_desc.Description,
    ) -> Self:
        """Get topic description.

        Raises
        ------
        ValueError
            The topic does not have a tool named `tool_name`.
        """
        try:
            return cls(topic_description.name())
        except ValueError as exc:
            _LOGGER.exception(
                "Unknown topic `%s`",
                topic_description.name(),
            )
            raise ValueError from exc

    @abstractmethod
    def to_description(self) -> abc_topic_desc.Description:
        """Get tool description."""
        raise NotImplementedError


class Tools(StrEnum):
    """Topic tools."""

    @classmethod
    def from_description(
        cls,
        tool_description: abc_tool_desc.Description,
    ) -> Self:
        """Get tool description.

        Raises
        ------
        ValueError
            The topic does not have a tool named `tool_name`.
        """
        try:
            return cls(tool_description.name())
        except ValueError as exc:
            _LOGGER.exception(
                "Unknown tool `%s` for topic `%s`",
                tool_description.name(),
                tool_description.name(),
            )
            raise ValueError from exc

    @abstractmethod
    def to_description(self) -> abc_tool_desc.Description:
        """Get tool description."""
        raise NotImplementedError
