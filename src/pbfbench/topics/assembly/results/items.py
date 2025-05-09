"""Assembly results.

All the assembly tools must have a common set of results.
"""

from __future__ import annotations

from pathlib import Path
from typing import final

import pbfbench.abc.topic.results.items as topic_res_items
import pbfbench.samples.file_system as smp_fs


@final
class FastaGZ(topic_res_items.Original):
    """FASTA gunzip result."""

    FASTA_GZ_NAME = Path("assembly.fasta.gz")

    @classmethod
    def fasta_gz(cls, sample_fs_manager: smp_fs.Manager) -> Path:
        """Get assembly FASTA file."""
        return sample_fs_manager.sample_dir() / cls.FASTA_GZ_NAME


@final
class AsmGraphGZ(topic_res_items.Original):
    """Assembly graph (GFA) gunzip result."""

    ASSEMBLY_GFA_GZ_NAME = Path("assembly.gfa.gz")

    @classmethod
    def gfa_gz(cls, sample_fs_manager: smp_fs.Manager) -> Path:
        """Get assembly GFA file."""
        return sample_fs_manager.sample_dir() / cls.ASSEMBLY_GFA_GZ_NAME
