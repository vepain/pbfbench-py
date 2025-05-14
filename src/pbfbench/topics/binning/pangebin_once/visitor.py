"""Concrete tool connector module."""

from typing import final

import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.topics.assembly.results.visitor as asm_res_visitor
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.binning.pangebin_once.config as pangebin_once_cfg
import pbfbench.topics.binning.pangebin_once.description as pangebin_once_desc
import pbfbench.topics.binning.pangebin_once.shell as pangebin_once_sh
import pbfbench.topics.plasmidness.pbf_input.results as plm_pbf_in_res
import pbfbench.topics.plasmidness.visitor as plm_visitor
import pbfbench.topics.seeds.pbf_input.results as seeds_pbf_in_res
import pbfbench.topics.seeds.visitor as seeds_visitor


@final
class Connector(
    abc_tool_visitor.ConnectorWithArguments[
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
        pangebin_once_cfg.Names.GFA: abc_tool_visitor.ArgumentPath(
            asm_visitor.Tools,
            asm_res_visitor.AsmGraphGZ,
            pangebin_once_sh.GFAInputLinesBuilder,
        ),
        pangebin_once_cfg.Names.SEEDS: abc_tool_visitor.ArgumentPath(
            seeds_visitor.Tools,
            seeds_pbf_in_res.SeedsVisitor,
            pangebin_once_sh.SeedsInputLinesBuilder,
        ),
        pangebin_once_cfg.Names.PLASMIDNESS: abc_tool_visitor.ArgumentPath(
            plm_visitor.Tools,
            plm_pbf_in_res.PlasmidnessVisitor,
            pangebin_once_sh.PlasmidnessInputLinesBuilder,
        ),  # FIXME how to verify the link between classes because no errors raised
    },
)
