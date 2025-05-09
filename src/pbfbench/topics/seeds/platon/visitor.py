"""Platon connector module."""

from typing import final

import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.topics.assembly.results.visitor as asm_res_visitor
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.seeds.platon.config as platon_cfg
import pbfbench.topics.seeds.platon.description as platon_desc
import pbfbench.topics.seeds.platon.shell as platon_sh


@final
class Connector(abc_tool_visitor.Connector[platon_cfg.Names]):
    """Platon connector."""

    @classmethod
    def config_type(cls) -> type[platon_cfg.ExpConfig]:
        """Get experiment config type."""
        return platon_cfg.ExpConfig


CONNECTOR = Connector(
    platon_desc.DESCRIPTION,
    {
        platon_cfg.Names.GENOME: abc_tool_visitor.ArgumentPath(
            asm_visitor.Tools,
            asm_res_visitor.FastaGZ,
            platon_sh.GenomeInputLinesBuilder,
        ),
    },
)
