"""Assembly results.

All the assembly tools must have a common set of results.
"""

from __future__ import annotations

from pathlib import Path
from typing import final

import pbfbench.abc.topic.results.items as topic_res_items


@final
class FastaGZ(topic_res_items.Original):
    """FASTA gunzip result."""

    FASTA_GZ_NAME = Path("assembly.fasta.gz")

    def fasta_gz(self, sample_dirname: str | Path) -> Path:
        """Get assembly FASTA file."""
        return self._fs_manager.sample_dir(sample_dirname) / self.FASTA_GZ_NAME


@final
class AsmGraphGZ(topic_res_items.Original):
    """Assembly graph (GFA) gunzip result."""

    ASSEMBLY_GFA_GZ_NAME = Path("assembly.gfa.gz")

    def gfa_gz(self, sample_dirname: str | Path) -> Path:
        """Get assembly GFA file."""
        return self._fs_manager.sample_dir(sample_dirname) / self.ASSEMBLY_GFA_GZ_NAME
