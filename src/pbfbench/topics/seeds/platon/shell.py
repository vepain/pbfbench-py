"""Platon Bash script logics."""

from collections.abc import Iterator
from typing import final

import pbfbench.abc.tool.shell as abc_tool_shell
import pbfbench.samples.shell as smp_sh
import pbfbench.shell as sh
import pbfbench.topics.assembly.results.items as asm_results
import pbfbench.topics.seeds.platon.config as platon_cfg


@final
class GenomeInputLinesBuilder(
    abc_tool_shell.ArgBashLinesBuilder[asm_results.FastaGZ],
):
    """Genome input bash lines builder."""

    FASTA_GZ_VAR = sh.Variable("fasta_gz")
    FASTA_VAR = sh.Variable("fasta")

    def init_lines(self) -> Iterator[str]:
        """Get shell input init lines."""
        fasta_gz_path = self._tool_data_result.fasta_gz(
            smp_sh.SpeSmpIDLinesBuilder.SPE_SMP_ID_VAR.eval(),
        )
        yield self.FASTA_GZ_VAR.set(sh.path_to_str(fasta_gz_path))
        yield f"gunzip -k {sh.path_to_str(self.FASTA_GZ_VAR.eval())}"
        yield self.FASTA_VAR.set(sh.path_to_str(f"${{{self.FASTA_GZ_VAR.name()}%.gz}}"))

    def argument(self) -> str:
        """Get shell input param lines."""
        return sh.path_to_str(self.FASTA_VAR.eval())

    def close_lines(self) -> Iterator[str]:
        """Get shell input close lines."""
        yield f"rm -f {sh.path_to_str(self.FASTA_VAR.eval())}"


@final
class Commands(abc_tool_shell.Commands[platon_cfg.Names, platon_cfg.Options]):
    """Platon commands."""

    def core_commands(self) -> Iterator[str]:
        """Iterate over the tool commands."""
        outdir = smp_sh.sample_sh_var_fs_manager(
            self._working_exp_fs_manager,
        ).sample_dir()
        # REFACTOR how to generalize according to different options types?
        yield (
            "platon "
            + " ".join(self._options)
            + f' --output "{outdir}"'
            + " "
            + self.argument(platon_cfg.Names.GENOME)
        )
