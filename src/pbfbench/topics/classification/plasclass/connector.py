"""PlasClass connector module."""

from typing import final

import pbfbench.abc.tool.connector as abc_tool_connector
import pbfbench.topics.assembly.results as asm_res
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.classification.plasclass.config as plasclass_cfg
import pbfbench.topics.classification.plasclass.description as plasclass_desc
import pbfbench.topics.classification.plasclass.shell as plasclass_sh


@final
class Connector(
    abc_tool_connector.ConnectorWithArguments[
        plasclass_cfg.Names,
        plasclass_cfg.ExpConfig,
    ],
):
    """PlasClass connector."""

    @classmethod
    def config_type(cls) -> type[plasclass_cfg.ExpConfig]:
        """Get experiment config type."""
        return plasclass_cfg.ExpConfig


CONNECTOR = Connector(
    plasclass_desc.DESCRIPTION,
    {
        plasclass_cfg.Names.FASTA: abc_tool_connector.ArgumentPath(
            asm_visitor.Tools,
            asm_res.FastaGZVisitor,
            plasclass_sh.FastaInputLinesBuilder,
        ),
    },
)
