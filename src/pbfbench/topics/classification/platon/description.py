"""Platon description module."""

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.topics.classification.description as class_desc

DESCRIPTION = abc_tool_desc.Description(
    "PLATON",
    "platon",
    class_desc.DESCRIPTION,
)
