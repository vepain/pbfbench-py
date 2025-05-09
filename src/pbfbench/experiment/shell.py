"""Tools script logics."""

from __future__ import annotations

import stat
from itertools import chain
from typing import TYPE_CHECKING

import pbfbench.abc.tool.environments as abc_tools_envs
import pbfbench.abc.tool.shell as abc_tool_shell
import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.shell as smp_sh
import pbfbench.shell as sh
import pbfbench.slurm.config as slurm_cfg
import pbfbench.slurm.shell as slurm_sh

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path


def create_run_script(
    data_fs_manager: exp_fs.Manager,
    work_fs_manager: exp_fs.Manager,
    samples_to_run: Iterable[smp_fs.RowNumberedItem],
    slurm_cfg: slurm_cfg.Config,
    tool_cmd: abc_tool_shell.Commands,
) -> None:
    """Create the run script."""
    tool_bash_env_wrapper = abc_tools_envs.BashEnvWrapper(
        data_fs_manager.tool_env_script_sh(),
    )

    _write_command_script(
        data_fs_manager,
        work_fs_manager,
        tool_cmd,
    )

    _add_x_permissions_to_command_script(work_fs_manager.command_sh_script())

    _write_sbatch_script(
        work_fs_manager,
        slurm_cfg,
        samples_to_run,
        tool_bash_env_wrapper,
    )


def _write_command_script(
    data_fs_manager: exp_fs.Manager,
    work_fs_manager: exp_fs.Manager,
    tool_cmd: abc_tool_shell.Commands,
) -> None:
    """Write the command script (which `srun` will call)."""
    cmd_sh_path = work_fs_manager.command_sh_script()
    with cmd_sh_path.open("w") as command_out:
        command_out.write(f"{sh.BASH_SHEBANG}\n\n")
        for line in chain(
            smp_sh.SpeSmpIDLinesBuilder(data_fs_manager.samples_tsv()).lines(),
            tool_cmd.commands(),
        ):
            command_out.write(sh.exit_on_error(line) + "\n")


def _add_x_permissions_to_command_script(cmd_sh_path: Path) -> None:
    """Chmod +x the subscript (called by `srun`) for everyone."""
    st = cmd_sh_path.stat()
    cmd_sh_path.chmod(st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _write_sbatch_script(
    work_fs_manager: exp_fs.Manager,
    slurm_cfg: slurm_cfg.Config,
    samples_to_run: Iterable[smp_fs.RowNumberedItem],
    tool_bash_env_wrapper: abc_tools_envs.BashEnvWrapper,
) -> None:
    """Write the sbatch script."""
    with work_fs_manager.sbatch_sh_script().open("w") as sbatch_out:
        sbatch_out.write(f"{sh.BASH_SHEBANG}\n")

        for line in chain(
            #
            # Sbatch comments
            #
            slurm_sh.SbatchCommentLinesBuilder.lines(
                slurm_cfg,
                (smp_fs.to_line_number_base_one(sample) for sample in samples_to_run),
                work_fs_manager,
            ),
            #
            # Write array job id in file
            #
            _write_slurm_array_job_id(work_fs_manager),
            #
            # Define exit functions
            #
            slurm_sh.ExitFunctionLinesBuilder.lines(work_fs_manager),
            #
            # Init env
            #
            (
                sh.manage_error_and_exit(
                    line,
                    slurm_sh.ExitFunctionLinesBuilder.EXIT_INIT_ENV_ERROR_FN_NAME,
                )
                for line in tool_bash_env_wrapper.init_env_lines()
            ),
            #
            # Srun command subscript
            #
            iter(
                (
                    sh.manage_error_and_exit(
                        f"srun {work_fs_manager.command_sh_script()}",
                        slurm_sh.ExitFunctionLinesBuilder.EXIT_COMMAND_ERROR_FN_NAME,
                    ),
                ),
            ),
            #
            # Close env
            #
            (
                sh.manage_error_and_exit(
                    line,
                    slurm_sh.ExitFunctionLinesBuilder.EXIT_CLOSE_ENV_ERROR_FN_NAME,
                )
                for line in tool_bash_env_wrapper.close_env_lines()
            ),
            #
            # Exit end
            #
            iter((slurm_sh.ExitFunctionLinesBuilder.EXIT_END_FN_NAME,)),
        ):
            sbatch_out.write(line + "\n")


def _write_slurm_array_job_id(work_fs_manager: exp_fs.Manager) -> Iterator[str]:
    """Return new command that exits the whole pipeline if first command fails."""
    yield f"if [[ ! -f {sh.path_to_str(work_fs_manager.array_job_id_file())} ]]; then"
    yield (
        f"\techo {slurm_sh.SLURM_ARRAY_JOB_ID_VAR.eval()}"
        f"> {sh.path_to_str(work_fs_manager.array_job_id_file())}"
    )
    yield "fi"
