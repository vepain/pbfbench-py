"""Assembly topic visitor."""

from typing import final

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.topics.assembly.gfa_connector.description as gfa_connector_desc
import pbfbench.topics.assembly.skesa.description as skesa_desc
import pbfbench.topics.assembly.unicycler.description as unicycler_desc


@final
class Tools(abc_topic_visitor.Tools):
    """Assembly tools descriptions."""

    UNICYCLER = unicycler_desc.DESCRIPTION.name()
    SKESA = skesa_desc.DESCRIPTION.name()
    GFA_CONNECTOR = gfa_connector_desc.DESCRIPTION.name()

    def to_description(self) -> abc_tool_desc.Description:
        """Get tool description."""
        match self:
            case Tools.UNICYCLER:
                return unicycler_desc.DESCRIPTION
            case Tools.SKESA:
                return skesa_desc.DESCRIPTION
            case Tools.GFA_CONNECTOR:
                return gfa_connector_desc.DESCRIPTION
