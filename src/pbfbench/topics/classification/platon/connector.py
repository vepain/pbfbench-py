"""Platon connector module."""

from typing import final

import pbfbench.abc.tool.connector as abc_tool_connector
import pbfbench.topics.assembly.results as asm_res
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.classification.platon.config as platon_cfg
import pbfbench.topics.classification.platon.description as platon_desc
import pbfbench.topics.classification.platon.shell as platon_sh


@final
class Connector(
    abc_tool_connector.ConnectorWithArguments[platon_cfg.Names, platon_cfg.ExpConfig],
):
    """Platon connector."""

    @classmethod
    def config_type(cls) -> type[platon_cfg.ExpConfig]:
        """Get experiment config type."""
        return platon_cfg.ExpConfig


CONNECTOR = Connector(
    platon_desc.DESCRIPTION,
    {
        platon_cfg.Names.GENOME: abc_tool_connector.ArgumentPath(
            asm_visitor.Tools,
            asm_res.FastaGZVisitor,
            platon_sh.GenomeInputLinesBuilder,
        ),
    },
)
