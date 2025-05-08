"""Sample bash script logics."""

from collections.abc import Iterator
from pathlib import Path

import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.items as smp_items
import pbfbench.shell as sh
from pbfbench import slurm


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
        yield (
            f"echo {slurm.SLURM_ARRAY_TASK_ID_VAR.eval()} {self.SPE_SMP_ID_VAR.eval()}"
        )

    def __get_sample_attribute(self, attribute: smp_fs.TSVHeader) -> str:
        """Get sample attribute."""
        attribute_column_index = smp_fs.columns_name_index(self.__samples_file)[
            attribute
        ]
        return (
            f"$("
            f'sed -n "{slurm.SLURM_ARRAY_TASK_ID_VAR.eval()}p"'
            f" {self.SAMPLES_FILE_VAR.eval()}"
            f" | cut -f{1 + attribute_column_index}"
            f")"
        )


def sample_shell_fs_manager(exp_fs_manager: exp_fs.Manager) -> smp_fs.Manager:
    """Get sample shell variable file system manager."""
    return smp_fs.Manager(
        exp_fs_manager.sample_dir(SpeSmpIDLinesBuilder.SPE_SMP_ID_VAR.eval()),
    )


def write_slurm_job_id(sample_fs_manager: smp_fs.Manager) -> str:
    """Return new command that exits the whole pipeline if first command fails."""
    return (
        f"echo {slurm.SLURM_JOB_ID_FROM_VARS}"
        f"> {sh.path_to_str(sample_fs_manager.slurm_job_id_file())}"
    )


EXIT_ERROR_FN_NAME = "exit_error"


def exit_error_function_lines(
    work_fs_manager: exp_fs.Manager,
    sample_fs_manager: smp_fs.Manager,
) -> Iterator[str]:
    """Iterate over bash lines describing the exit error function."""
    yield f"function {EXIT_ERROR_FN_NAME}" + " {"
    yield f'  cp "{slurm.err_log_job_var_path(work_fs_manager)}" "{sample_fs_manager.errors_log()}"'  # noqa: E501
    yield "  exit 1"
    yield "}"


def manage_error_and_exit(command: str) -> str:
    """Return new command that exits the whole pipeline if first command fails."""
    if sh.is_a_command(command):
        return command + " || " + EXIT_ERROR_FN_NAME
    return command


def write_done_log(
    work_fs_manager: exp_fs.Manager,
    sample_fs_manager: smp_fs.Manager,
) -> str:
    """Return new command that exits the whole pipeline if first command fails."""
    return (
        f"cp {slurm.out_log_job_var_path(work_fs_manager)}"
        f" {sample_fs_manager.done_log()}"
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
    # samples_file.unlink()
