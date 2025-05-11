"""Plasmidness topic visitor."""

from typing import final

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.topics.plasmidness.plasclass.description as plasclass_desc


@final
class Tools(abc_topic_visitor.Tools):
    """Plasmidness tools descriptions."""

    PLASCLASS = plasclass_desc.DESCRIPTION.name()

    def to_description(self) -> abc_tool_desc.Description:
        """Get tool description."""
        match self:
            case Tools.PLASCLASS:
                return plasclass_desc.DESCRIPTION
