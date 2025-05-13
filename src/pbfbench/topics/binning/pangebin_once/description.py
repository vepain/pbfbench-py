"""Tool description."""

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.topics.binning.description as bin_desc

DESCRIPTION = abc_tool_desc.Description(
    "PANGEBIN_ONCE",
    "pangebin-once",
    bin_desc.DESCRIPTION,
)
