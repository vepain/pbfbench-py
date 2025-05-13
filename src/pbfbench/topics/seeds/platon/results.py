"""Tool results."""

from __future__ import annotations

from pathlib import Path
from typing import final

import pbfbench.abc.topic.results.items as topic_res_items
import pbfbench.topics.assembly.results.items as asm_res_items


@final
class PlasmidStats(topic_res_items.Original):
    """Plasmid stats result."""

    TSV_NAME = asm_res_items.FastaGZ.FASTA_GZ_NAME.with_suffix(".tsv")

    def tsv(self, sample_dirname: str | Path) -> Path:
        """Get TSV file."""
        return self._exp_fs_manager.sample_dir(sample_dirname) / self.TSV_NAME
