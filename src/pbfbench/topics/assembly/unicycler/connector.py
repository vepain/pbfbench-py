"""Connector for Unicycler."""

# Due to typer usage:

from __future__ import annotations

from typing import final

import pbfbench.abc.tool.connector as abc_tool_connector
import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.topics.assembly.unicycler.description as unicycler_desc


@final
class Connector(abc_tool_connector.OnlyOptions):
    """Unicycler connector."""

    @classmethod
    def description(cls) -> abc_tool_desc.Description:
        """Get description."""
        return unicycler_desc.DESCRIPTION
