"""PlasClass connector module."""

from typing import final

import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.topics.assembly.results.visitor as asm_res_visitor
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.plasmidness.plasclass.config as plasclass_cfg
import pbfbench.topics.plasmidness.plasclass.description as plasclass_desc
import pbfbench.topics.plasmidness.plasclass.shell as plasclass_sh


@final
class Connector(abc_tool_visitor.Connector[plasclass_cfg.Names]):
    """PlasClass connector."""

    @classmethod
    def config_type(cls) -> type[plasclass_cfg.ExpConfig]:
        """Get experiment config type."""
        return plasclass_cfg.ExpConfig


CONNECTOR = Connector(
    plasclass_desc.DESCRIPTION,
    {
        plasclass_cfg.Names.FASTA: abc_tool_visitor.ArgumentPath(
            asm_visitor.Tools,
            asm_res_visitor.FastaGZ,
            plasclass_sh.FastaInputLinesBuilder,
        ),
    },
)
