"""Platon connector module."""

from typing import final

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.topics.assembly.results.visitor as asm_res_visitor
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.seeds.platon.config as platon_cfg
import pbfbench.topics.seeds.platon.description as platon_desc
import pbfbench.topics.seeds.platon.shell as platon_sh


@final
class Connector(
    abc_tool_visitor.Connector[
        platon_cfg.Names,
        platon_cfg.Config,
        platon_sh.Commands,
    ],
):
    """Platon connectors."""

    @classmethod
    def config_type(cls) -> type[platon_cfg.Config]:
        """Get config type."""
        return platon_cfg.Config

    @classmethod
    def commands_type(cls) -> type[platon_sh.Commands]:
        """Get commands type."""
        return platon_sh.Commands

    @classmethod
    def tool_description(cls) -> abc_tool_desc.Description:
        """Get tool description."""
        return platon_desc.DESCRIPTION


CONNECTOR = Connector(
    {
        platon_cfg.Names.GENOME: abc_tool_visitor.ArgumentPath(
            asm_visitor.Tools,
            asm_res_visitor.fasta_gz,
            platon_sh.GenomeInputLinesBuilder,
        ),
    },
)
