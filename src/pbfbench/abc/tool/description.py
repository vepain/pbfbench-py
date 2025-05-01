"""Tool description abstract module."""

import pbfbench.abc.topic.description as abc_topic_desc


class Description:
    """Tool description."""

    def __init__(
        self,
        name: str,
        cmd: str,
        topic_description: abc_topic_desc.Description,
    ) -> None:
        self.__name = name
        self.__cmd = cmd
        self.__topic_description = topic_description

    def name(self) -> str:
        """Get name."""
        return self.__name

    def cmd(self) -> str:
        """Get command."""
        return self.__cmd

    def topic(self) -> abc_topic_desc.Description:
        """Get topic description."""
        return self.__topic_description
