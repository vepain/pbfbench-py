"""Platon description module."""

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.topics.seeds.description as seeds_desc

DESCRIPTION = abc_tool_desc.Description(
    "PLATON",
    "platon",
    seeds_desc.DESCRIPTION,
)
