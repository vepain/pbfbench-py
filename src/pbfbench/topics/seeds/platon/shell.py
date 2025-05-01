"""Platon Bash script logics."""

from collections.abc import Iterator

import pbfbench.abc.tool.shell as abc_tool_shell
import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.shell as smp_sh
import pbfbench.shell as sh
import pbfbench.topics.assembly.results.items as asm_results
import pbfbench.topics.seeds.platon.config as platon_cfg


class GenomeInputLinesBuilder(
    abc_tool_shell.ArgBashLinesBuilder[asm_results.FastaGZ],
):
    """Genome input bash lines builder."""

    FASTA_GZ_VAR = sh.Variable("fasta_gz")
    FASTA_VAR = sh.Variable("fasta")

    def sh_init_lines(self) -> Iterator[str]:
        """Get shell input init lines."""
        fasta_gz_path = self.__tool_data_result.fasta_gz(
            smp_sh.SpeSmpIDLinesBuilder.SPE_SMP_ID_VAR.eval(),
        )
        yield self.FASTA_GZ_VAR.set(sh.path_to_str(fasta_gz_path))
        yield f'gunzip -k "{self.FASTA_GZ_VAR.eval()}"'
        yield self.FASTA_VAR.set(f'"${{{self.FASTA_GZ_VAR.name()}%.gz}}"')

    def sh_param_lines(self) -> Iterator[str]:
        """Get shell input param lines."""
        yield f'"{self.FASTA_VAR.eval()}"'

    def sh_close_lines(self) -> Iterator[str]:
        """Get shell input close lines."""
        yield f'rm -f "{self.FASTA_VAR.eval()}"'


class Commands(abc_tool_shell.Commands[platon_cfg.Options]):
    """Platon commands."""

    def __init__(
        self,
        in_genome_sh_builder: GenomeInputLinesBuilder,
        options: platon_cfg.Options,
        working_exp_fs_manager: exp_fs.Manager,
    ) -> None:
        self.__in_genome_sh_builder = in_genome_sh_builder
        super().__init__(options, working_exp_fs_manager)

    def commands(self) -> Iterator[str]:
        """Iterate over the tool commands."""
        outdir = smp_sh.sample_sh_var_fs_manager(
            self.__working_exp_fs_manager,
        ).sample_dir()
        yield from self.__in_genome_sh_builder.sh_init_lines()
        yield ""
        yield (
            "platon "
            + " ".join(self.__options)
            + f' --output "{outdir}"'
            + " "
            + " ".join(self.__in_genome_sh_builder.sh_param_lines())
        )
        yield ""
        yield from self.__in_genome_sh_builder.sh_close_lines()
