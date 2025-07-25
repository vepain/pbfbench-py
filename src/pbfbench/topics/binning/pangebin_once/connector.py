"""Concrete tool connector module."""

from typing import final

import pbfbench.abc.tool.connector as abc_tool_connector
import pbfbench.topics.assembly.results as asm_res
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.binning.pangebin_once.config as pangebin_once_cfg
import pbfbench.topics.binning.pangebin_once.description as pangebin_once_desc
import pbfbench.topics.binning.pangebin_once.shell as pangebin_once_sh
import pbfbench.topics.classification.pbf_input.results as class_pbf_in_res
import pbfbench.topics.classification.visitor as class_visitor


@final
class Connector(
    abc_tool_connector.ConnectorWithArguments[
        pangebin_once_cfg.Names,
        pangebin_once_cfg.ExpConfig,
    ],
):
    """Connector."""

    @classmethod
    def config_type(cls) -> type[pangebin_once_cfg.ExpConfig]:
        """Get experiment config type."""
        return pangebin_once_cfg.ExpConfig


CONNECTOR = Connector(
    pangebin_once_desc.DESCRIPTION,
    {
        pangebin_once_cfg.Names.GFA: abc_tool_connector.ArgumentPath[
            asm_visitor.Tools,
            asm_res.AsmGraphGZ,
        ](
            asm_visitor.Tools,
            asm_res.AsmGraphGZVisitor,
            pangebin_once_sh.GFAInputLinesBuilder,
        ),
        pangebin_once_cfg.Names.SEEDS: abc_tool_connector.ArgumentPath[
            class_visitor.Tools,
            class_pbf_in_res.Seeds,
        ](
            class_visitor.Tools,
            class_pbf_in_res.SeedsVisitor,
            pangebin_once_sh.SeedsInputLinesBuilder,
        ),
        pangebin_once_cfg.Names.PLASMIDNESS: abc_tool_connector.ArgumentPath[
            class_visitor.Tools,
            class_pbf_in_res.Plasmidness,
        ](
            class_visitor.Tools,
            class_pbf_in_res.PlasmidnessVisitor,
            pangebin_once_sh.PlasmidnessInputLinesBuilder,
        ),
    },
)
