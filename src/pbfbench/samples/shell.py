"""Sample bash script logics."""

from collections.abc import Iterator
from pathlib import Path

import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.items as smp_items
import pbfbench.shell as sh
import pbfbench.slurm.shell as slurm_sh


class SpeSmpIDLinesBuilder:
    """Species-sample ID bash lines builder.

    The bash variable name is: `cls.SPE_SAM_ID_VARNAME`

    The species-sample id is defined as:
    `{species_id}-{sample_id}`
    """

    SAMPLES_FILE_VAR = sh.Variable("samples_file")

    SPECIES_ID_VAR = sh.Variable("species_id")
    SAMPLE_ID_VAR = sh.Variable("sample_id")
    SPE_SMP_ID_VAR = sh.Variable("species_sample_id")

    def __init__(self, samples_file: Path) -> None:
        """Initialize."""
        self.__samples_file = samples_file

    def samples_file(self) -> Path:
        """Get samples file."""
        return self.__samples_file

    def lines(self) -> Iterator[str]:
        """Give the bash lines defining the species-sample id variable."""
        yield self.SAMPLES_FILE_VAR.set(sh.path_to_str(self.__samples_file))
        yield self.SAMPLE_ID_VAR.set(
            self.__get_sample_attribute(smp_fs.TSVHeader.SAMPLE_ID),
        )
        yield self.SPECIES_ID_VAR.set(
            self.__get_sample_attribute(smp_fs.TSVHeader.SPECIES_ID),
        )
        yield self.SPE_SMP_ID_VAR.set(
            smp_items.fmt_exp_sample_id(
                self.SPECIES_ID_VAR.eval(),
                self.SAMPLE_ID_VAR.eval(),
            ),
        )
        yield f"echo {self.SPE_SMP_ID_VAR.eval()}"

    def __get_sample_attribute(self, attribute: smp_fs.TSVHeader) -> str:
        """Get sample attribute."""
        attribute_column_index = smp_fs.columns_name_index(self.__samples_file)[
            attribute
        ]
        return (
            f"$("
            f'sed -n "{slurm_sh.SLURM_ARRAY_TASK_ID_VAR.eval()}p"'
            f" {self.SAMPLES_FILE_VAR.eval()}"
            f" | cut -f{1 + attribute_column_index}"
            f")"
        )


def sample_shell_fs_manager(exp_fs_manager: exp_fs.ManagerBase) -> smp_fs.Manager:
    """Get sample shell variable file system manager."""
    return smp_fs.Manager(
        exp_fs_manager.sample_dir(SpeSmpIDLinesBuilder.SPE_SMP_ID_VAR.eval()),
    )


if __name__ == "__main__":
    from rich.markdown import Markdown as Md

    from pbfbench import root_logging

    samples_file = Path("samples.tsv")
    with samples_file.open("w") as f_out:
        f_out.write(f"{smp_fs.TSVHeader.SPECIES_ID}\t{smp_fs.TSVHeader.SAMPLE_ID}\n")
        f_out.write("sp1\tsmp1\n")
        f_out.write("sp2\tsmp2\n")
        f_out.write("sp3\tsmp3\n")

    sh_builder = SpeSmpIDLinesBuilder(samples_file)
    bash_lines = "\n".join(sh_builder.lines())
    root_logging.CONSOLE.print(Md(f"```bash\n{bash_lines}\n```"))
