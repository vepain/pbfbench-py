"""Tool results."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

import pbfbench.abc.topic.results as abc_topic_res
import pbfbench.topics.assembly.results as asm_res

if TYPE_CHECKING:
    from pathlib import Path


@final
class PlasmidStats(abc_topic_res.Original):
    """Plasmid stats result."""

    # TSV name: "assembly.tsv"
    # (no .fasta because Platon removes it, no .gz because PLaton took a gunzip FASTA)
    TSV_NAME = asm_res.FastaGZ.FASTA_GZ_NAME.with_suffix("").with_suffix(".tsv")

    def tsv(self, sample_dirname: str | Path) -> Path:
        """Get TSV file."""
        return self._exp_fs_manager.sample_dir(sample_dirname) / self.TSV_NAME
