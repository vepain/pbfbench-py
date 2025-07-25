"""Plasmidness topic visitor."""

from typing import final

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.abc.topic.visitor as abc_topic_visitor

from .plasclass import description as plasclass_desc
from .plasgraph2 import description as plasgraph2_desc
from .platon import description as platon_desc


@final
class Tools(abc_topic_visitor.Tools):
    """Plasmidness tools descriptions."""

    PLASCLASS = plasclass_desc.DESCRIPTION.name()
    PLASGRAPH2 = plasgraph2_desc.DESCRIPTION.name()
    PLATON = platon_desc.DESCRIPTION.name()

    def to_description(self) -> abc_tool_desc.Description:
        """Get tool description."""
        match self:
            case Tools.PLASCLASS:
                return plasclass_desc.DESCRIPTION
            case Tools.PLASGRAPH2:
                return plasgraph2_desc.DESCRIPTION
            case Tools.PLATON:
                return platon_desc.DESCRIPTION
