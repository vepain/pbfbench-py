"""plASgraph2 connector module."""

from typing import final

import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.topics.assembly.results.visitor as asm_res_visitor
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.plasmidness.plasgraph2.config as plasgraph2_cfg
import pbfbench.topics.plasmidness.plasgraph2.description as plasgraph2_desc
import pbfbench.topics.plasmidness.plasgraph2.shell as plasgraph2_sh


@final
class Connector(
    abc_tool_visitor.ConnectorWithArguments[
        plasgraph2_cfg.Names,
        plasgraph2_cfg.ExpConfig,
    ],
):
    """Connector."""

    @classmethod
    def config_type(cls) -> type[plasgraph2_cfg.ExpConfig]:
        """Get experiment config type."""
        return plasgraph2_cfg.ExpConfig


CONNECTOR = Connector(
    plasgraph2_desc.DESCRIPTION,
    {
        plasgraph2_cfg.Names.GFA: abc_tool_visitor.ArgumentPath(
            asm_visitor.Tools,
            asm_res_visitor.AsmGraphGZ,
            plasgraph2_sh.GFAInputLinesBuilder,
        ),
    },
)
