"""Seeds topic visitor."""

from typing import final

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.topics.seeds.platon.description as platon_desc


@final
class Tools(abc_topic_visitor.Tools):
    """Assembly tools descriptions."""

    PLATON = platon_desc.DESCRIPTION.name()

    def to_description(self) -> abc_tool_desc.Description:
        """Get tool description."""
        match self:
            case Tools.PLATON:
                return platon_desc.DESCRIPTION
