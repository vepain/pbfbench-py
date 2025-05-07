"""Assembly result visitors."""

import logging
from typing import final

import pbfbench.abc.topic.results.visitors as topic_res_visitors
import pbfbench.topics.assembly.results.items as asm_res_items
import pbfbench.topics.assembly.visitor as asm_visitor

# REFACTOR if the logic is up to asm_resuls, do not repeat(?)
# How to decide:
# - transform specific tool result to std pbfbench result (e.g. GFA to GFA.gz)
# - specific result must have a visitor
# - which logic to get specific result to transform during sh line build?
#   - visitor takes as input a Tools: how to get Tools in sh builders?

_LOGGER = logging.getLogger(__name__)


@final
class FastaGZ(topic_res_visitors.Original):
    """FastaGZ result visitor."""

    @classmethod
    def result_builder(cls) -> type[asm_res_items.FastaGZ]:
        """Get result builder."""
        return asm_res_items.FastaGZ

    @classmethod
    def result_builder_from_tool(
        cls,
        tool: asm_visitor.Tools,
    ) -> type[asm_res_items.FastaGZ]:
        """Visit assembly FASTA tool result."""
        match tool:
            case asm_visitor.Tools.UNICYCLER:
                return asm_res_items.FastaGZ
            case asm_visitor.Tools.SKESA:
                return asm_res_items.FastaGZ
            case asm_visitor.Tools.GFA_CONNECTOR:
                _err_msg = (
                    f"{asm_visitor.Tools.GFA_CONNECTOR} tool"
                    " does not provide a FASTA file"
                    f" but {asm_visitor.Tools.SKESA} does"
                )
                raise ValueError(_err_msg)


@final
class AsmGraphGZ(topic_res_visitors.Original):
    """Assembly graph (GFA) result visitor."""

    @classmethod
    def result_builder(cls) -> type[asm_res_items.AsmGraphGZ]:
        """Get result builder."""
        return asm_res_items.AsmGraphGZ

    @classmethod
    def result_builder_from_tool(
        cls,
        tool: asm_visitor.Tools,
    ) -> type[asm_res_items.AsmGraphGZ]:
        """Visit assembly graph (GFA) tool result."""
        match tool:
            case asm_visitor.Tools.UNICYCLER:
                return asm_res_items.AsmGraphGZ
            case asm_visitor.Tools.SKESA:
                return asm_res_items.AsmGraphGZ
            case asm_visitor.Tools.GFA_CONNECTOR:
                _LOGGER.critical(
                    "%s tool do not provide a GFA file: %s does",
                    asm_visitor.Tools.GFA_CONNECTOR,
                    asm_visitor.Tools.SKESA,
                )  # REFACTOR move that to a check config function
                raise ValueError
