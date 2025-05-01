"""Assembly result visitors."""

import logging

import pbfbench.topics.assembly.results.items as asm_results
import pbfbench.topics.assembly.visitor as asm_visitor

# REFACTOR if the logic is up to asm_resuls, do not repeat(?)
# How to decide:
# - transform specific tool result to std pbfbench result (e.g. GFA to GFA.gz)
# - specific result must have a visitor
# - which logic to get specific result to transform during sh line build?
#   - visitor takes as input a Tools: how to get Tools in sh builders?

_LOGGER = logging.getLogger(__name__)


def fasta_gz(tool: asm_visitor.Tools) -> type[asm_results.FastaGZ]:
    """Visit assembly FASTA tool result."""
    match tool:
        case asm_visitor.Tools.UNICYCLER:
            return asm_results.FastaGZ
        case asm_visitor.Tools.SKESA:
            return asm_results.FastaGZ
        case asm_visitor.Tools.GFA_CONNECTOR:
            _LOGGER.critical(
                "%s tool do not provide a FASTA file: %s does",
                asm_visitor.Tools.GFA_CONNECTOR,
                asm_visitor.Tools.SKESA,
            )
            raise ValueError


def asm_graph_gz(tool: asm_visitor.Tools) -> type[asm_results.AsmGraphGZ]:
    """Visit assembly graph (GFA) tool result."""
    match tool:
        case asm_visitor.Tools.UNICYCLER:
            return asm_results.AsmGraphGZ
        case asm_visitor.Tools.SKESA:
            _LOGGER.critical(
                "%s tool do not provide a GFA file: %s does",
                asm_visitor.Tools.SKESA,
                asm_visitor.Tools.GFA_CONNECTOR,
            )
            raise ValueError
        case asm_visitor.Tools.GFA_CONNECTOR:
            return asm_results.AsmGraphGZ
