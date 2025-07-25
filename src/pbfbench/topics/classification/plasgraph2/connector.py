"""plASgraph2 connector module."""

from typing import final

import pbfbench.abc.tool.connector as abc_tool_connector
import pbfbench.topics.assembly.results as asm_res
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.classification.plasgraph2.config as plasgraph2_cfg
import pbfbench.topics.classification.plasgraph2.description as plasgraph2_desc
import pbfbench.topics.classification.plasgraph2.shell as plasgraph2_sh


@final
class Connector(
    abc_tool_connector.ConnectorWithArguments[
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
        plasgraph2_cfg.Names.GFA: abc_tool_connector.ArgumentPath(
            asm_visitor.Tools,
            asm_res.AsmGraphGZVisitor,
            plasgraph2_sh.GFAInputLinesBuilder,
        ),
    },
)
