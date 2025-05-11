"""plASgraph2 connector module."""

from typing import final

import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.topics.assembly.results.visitor as asm_res_visitor
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.plasmidness.plasgraphtwo.config as plasgraphtwo_cfg
import pbfbench.topics.plasmidness.plasgraphtwo.description as plasgraphtwo_desc
import pbfbench.topics.plasmidness.plasgraphtwo.shell as plasgraphtwo_sh


@final
class Connector(abc_tool_visitor.Connector[plasgraphtwo_cfg.Names]):
    """Connector."""

    @classmethod
    def config_type(cls) -> type[plasgraphtwo_cfg.ExpConfig]:
        """Get experiment config type."""
        return plasgraphtwo_cfg.ExpConfig


CONNECTOR = Connector(
    plasgraphtwo_desc.DESCRIPTION,
    {
        plasgraphtwo_cfg.Names.GFA: abc_tool_visitor.ArgumentPath(
            asm_visitor.Tools,
            asm_res_visitor.AsmGraphGZ,
            plasgraphtwo_sh.GFAInputLinesBuilder,
        ),
    },
)
