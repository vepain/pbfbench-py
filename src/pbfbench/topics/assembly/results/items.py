"""Assembly results.

All the assembly tools must have a common set of results.
"""

from __future__ import annotations

from abc import abstractmethod
from pathlib import Path

import pbfbench.abc.topic.results.items as tools_results


class FastaGZ(tools_results.Result):
    """FASTA gunzip result."""

    FASTA_GZ_NAME = Path("assembly.fasta.gz")

    @classmethod
    @abstractmethod
    def fasta_gz_path_from_sample_dir(cls) -> Path:
        """Get assembly FASTA file."""
        raise NotImplementedError

    def fasta_gz(self, sample_dirname: str) -> Path:
        """Get assembly FASTA file."""
        return self.__exp_fs_manager.sample_dir(sample_dirname) / self.FASTA_GZ_NAME


class AsmGraphGZ(tools_results.Result):
    """Assembly graph (GFA) gunzip result."""

    ASSEMBLY_GFA_GZ_NAME = Path("assembly.gfa.gz")

    def gfa_gz(self, sample_dirname: str) -> Path:
        """Get assembly GFA file."""
        return (
            self.__exp_fs_manager.sample_dir(sample_dirname) / self.ASSEMBLY_GFA_GZ_NAME
        )
