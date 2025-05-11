"""plASgraph2 description."""

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.topics.plasmidness.description as plasmidness_desc

DESCRIPTION = abc_tool_desc.Description(
    "PLASGRAPH2",
    "plasgraph2",
    plasmidness_desc.DESCRIPTION,
)
