"""Assembly results.

All the assembly tools must have a common set of results.
"""

from __future__ import annotations

from pathlib import Path
from typing import final

import pbfbench.abc.topic.results as abc_topic_res
import pbfbench.topics.assembly.visitor as asm_visitor


@final
class FastaGZ(abc_topic_res.Original):
    """FASTA gunzip result."""

    FASTA_GZ_NAME = Path("assembly.fasta.gz")

    def fasta_gz(self, sample_dirname: str | Path) -> Path:
        """Get assembly FASTA file."""
        return self._exp_fs_manager.sample_dir(sample_dirname) / self.FASTA_GZ_NAME


@final
class AsmGraphGZ(abc_topic_res.Original):
    """Assembly graph (GFA) gunzip result."""

    ASSEMBLY_GFA_GZ_NAME = Path("assembly.gfa.gz")

    def gfa_gz(self, sample_dirname: str | Path) -> Path:
        """Get assembly GFA file."""
        return (
            self._exp_fs_manager.sample_dir(sample_dirname) / self.ASSEMBLY_GFA_GZ_NAME
        )


@final
class FastaGZVisitor(abc_topic_res.OriginalVisitor):
    """FastaGZ result visitor."""

    @classmethod
    def result_builder(cls) -> type[FastaGZ]:
        """Get result builder."""
        return FastaGZ

    @classmethod
    def result_builder_from_tool(
        cls,
        tool: asm_visitor.Tools,
    ) -> abc_topic_res.Error | type[FastaGZ]:
        """Visit assembly FASTA tool result."""
        match tool:
            case asm_visitor.Tools.UNICYCLER:
                return cls.result_builder()
            case asm_visitor.Tools.SKESA:
                return cls.result_builder()
            case asm_visitor.Tools.GFA_CONNECTOR:
                return cls.result_builder()


@final
class AsmGraphGZVisitor(abc_topic_res.OriginalVisitor):
    """Assembly graph (GFA) result visitor."""

    @classmethod
    def result_builder(cls) -> type[AsmGraphGZ]:
        """Get result builder."""
        return AsmGraphGZ

    @classmethod
    def result_builder_from_tool(
        cls,
        tool: asm_visitor.Tools,
    ) -> abc_topic_res.Error | type[AsmGraphGZ]:
        """Visit assembly graph (GFA) tool result."""
        match tool:
            case asm_visitor.Tools.UNICYCLER:
                return cls.result_builder()
            case asm_visitor.Tools.SKESA:
                return abc_topic_res.Error(
                    f"{asm_visitor.Tools.SKESA} tool"
                    " does not provide a GFA file"
                    f" but {asm_visitor.Tools.GFA_CONNECTOR} does",
                )
            case asm_visitor.Tools.GFA_CONNECTOR:
                return cls.result_builder()
