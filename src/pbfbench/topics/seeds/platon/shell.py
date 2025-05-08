"""Platon Bash script logics."""

from collections.abc import Iterator
from pathlib import Path
from typing import final

import pbfbench.abc.tool.shell as abc_tool_shell
import pbfbench.shell as sh
import pbfbench.topics.assembly.results.items as asm_res_items


@final
class GenomeInputLinesBuilder(
    abc_tool_shell.ArgBashLinesBuilder[asm_res_items.FastaGZ],
):
    """Genome input bash lines builder."""

    GENOME_VAR = sh.Variable("GENOME")

    FASTA_GZ_VAR = sh.Variable("FASTA_GZ")

    def __fasta_gz_file(self) -> Path:
        """Return a gzipped FASTA path with sample name is a sh variable."""
        return self._input_result.fasta_gz(self._input_data_smp_sh_fs_manager)

    def __fasta_tmp_file(self) -> Path:
        """Return a tmp FASTA path with sample name is a sh variable."""
        return self._working_smp_sh_fs_manager.sample_dir() / "tmp_assembly.fasta"

    def init_lines(self) -> Iterator[str]:
        """Get shell input init lines."""
        yield self.FASTA_GZ_VAR.set(sh.path_to_str(self.__fasta_gz_file()))
        yield self.GENOME_VAR.set(sh.path_to_str(self.__fasta_tmp_file()))
        yield (
            "gunzip -k -c"
            f" {sh.path_to_str(self.FASTA_GZ_VAR.eval())}"
            f"> {sh.path_to_str(self.GENOME_VAR.eval())}"
        )

    def close_lines(self) -> Iterator[str]:
        """Get shell input close lines."""
        yield f"rm -f {sh.path_to_str(self.GENOME_VAR.eval())}"
