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
from pbfbench import slurm

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


def create_run_script(
    data_fs_manager: exp_fs.Manager,
    work_fs_manager: exp_fs.Manager,
    samples_to_run: Iterable[smp_fs.RowNumberedItem],
    slurm_cfg: slurm.Config,
    tool_cmd: abc_tool_shell.Commands,
) -> None:
    """Create the run script."""
    tool_bash_env_wrapper = abc_tools_envs.BashEnvWrapper(
        data_fs_manager.tool_env_script_sh(),
    )
    sample_fs_manager = smp_sh.sample_shell_fs_manager(work_fs_manager)

    _write_command_script(
        data_fs_manager,
        work_fs_manager,
        sample_fs_manager,
        tool_cmd,
    )

    _add_x_permissions_to_command_script(work_fs_manager.command_sh_script())

    _write_sbatch_script(
        work_fs_manager,
        sample_fs_manager,
        slurm_cfg,
        samples_to_run,
        tool_bash_env_wrapper,
    )


def _write_command_script(
    data_fs_manager: exp_fs.Manager,
    work_fs_manager: exp_fs.Manager,
    sample_fs_manager: smp_fs.Manager,
    tool_cmd: abc_tool_shell.Commands,
) -> None:
    """Write the command script (which `srun` will call)."""
    cmd_sh_path = work_fs_manager.command_sh_script()
    with cmd_sh_path.open("w") as command_out:
        command_out.write(f"{sh.BASH_SHEBANG}\n\n")
        for line in chain(
            smp_sh.SpeSmpIDLinesBuilder(
                smp_fs.samples_tsv(data_fs_manager.root_dir()),
            ).lines(),
            iter((smp_sh.write_slurm_job_id(sample_fs_manager),)),
            tool_cmd.commands(),
        ):
            command_out.write(sh.exit_on_error(line) + "\n")

        command_out.write(
            smp_sh.write_done_log(work_fs_manager, sample_fs_manager) + "\n",
        )


def _add_x_permissions_to_command_script(cmd_sh_path: Path) -> None:
    """Chmod +x the subscript (called by `srun`) for everyone."""
    st = cmd_sh_path.stat()
    cmd_sh_path.chmod(st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _write_sbatch_script(
    work_fs_manager: exp_fs.Manager,
    sample_fs_manager: smp_fs.Manager,
    slurm_cfg: slurm.Config,
    samples_to_run: Iterable[smp_fs.RowNumberedItem],
    tool_bash_env_wrapper: abc_tools_envs.BashEnvWrapper,
) -> None:
    """Write the sbatch script."""
    with work_fs_manager.sbatch_sh_script().open("w") as sbatch_out:
        sbatch_out.write(f"{sh.BASH_SHEBANG}\n")

        for line in chain(
            slurm.comment_lines(
                slurm_cfg,
                (sample.row_number() + 2 for sample in samples_to_run),
                work_fs_manager,
            ),
            smp_sh.exit_error_function_lines(work_fs_manager, sample_fs_manager),
            map(smp_sh.manage_error_and_exit, tool_bash_env_wrapper.init_env_lines()),
            iter(
                (
                    smp_sh.manage_error_and_exit(
                        f"srun {work_fs_manager.command_sh_script()}",
                    ),
                ),
            ),
            tool_bash_env_wrapper.close_env_lines(),
        ):
            sbatch_out.write(line + "\n")
