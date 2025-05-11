"""Platon Bash script logics."""

from collections.abc import Iterator
from pathlib import Path
from typing import final

import pbfbench.abc.tool.shell as abc_tool_shell
import pbfbench.shell as sh
import pbfbench.topics.assembly.results.items as asm_res_items
import pbfbench.topics.plasmidness.plasclass.results as plasclass_res


@final
class FastaInputLinesBuilder(
    abc_tool_shell.ArgBashLinesBuilder[asm_res_items.FastaGZ],
):
    """Fasta input bash lines builder."""

    FASTA_GZ_VAR = sh.Variable("FASTA_GZ")

    FASTA_VAR = sh.Variable("FASTA")
    OUTFILE_VAR = sh.Variable("OUTFILE")

    def __fasta_gz_file(self) -> Path:
        """Return a gzipped FASTA path with sample name is a sh variable."""
        return self._input_result.fasta_gz(
            self._input_data_smp_sh_fs_manager.sample_dir().name,
        )

    def __fasta_tmp_file(self) -> Path:
        """Return a tmp FASTA path with sample name is a sh variable."""
        return (
            self._work_smp_sh_fs_manager.sample_dir()
            / self._input_result.FASTA_GZ_NAME.with_suffix("")
        )

    def init_lines(self) -> Iterator[str]:
        """Get shell input init lines."""
        yield self.FASTA_GZ_VAR.set(sh.path_to_str(self.__fasta_gz_file()))
        yield self.FASTA_VAR.set(sh.path_to_str(self.__fasta_tmp_file()))
        yield self.OUTFILE_VAR.set(
            sh.path_to_str(
                plasclass_res.PlasmidProbabilities(self._work_exp_fs_manager).tsv(
                    self._work_smp_sh_fs_manager.sample_dir().name,
                ),
            ),
        )
        yield (
            "gunzip -k -c"
            f" {sh.path_to_str(self.FASTA_GZ_VAR.eval())}"
            f"> {sh.path_to_str(self.FASTA_VAR.eval())}"
        )

    def close_lines(self) -> Iterator[str]:
        """Get shell input close lines."""
        yield f"rm -f {sh.path_to_str(self.FASTA_VAR.eval())}"
