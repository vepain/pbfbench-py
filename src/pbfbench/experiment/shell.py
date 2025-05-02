"""Tools script logics."""

from __future__ import annotations

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
) -> Path:
    """Create the run script."""
    script_path = work_fs_manager.script_sh()
    tool_bash_env_wrapper = abc_tools_envs.BashEnvWrapper(
        data_fs_manager.tool_env_script_sh(),
    )
    sample_fs_manager = smp_sh.sample_sh_var_fs_manager(work_fs_manager)

    with script_path.open("w") as script_out:
        script_out.write(f"{sh.BASH_SHEBANG}\n")

        for line in chain(
            slurm.comment_lines(
                slurm_cfg,
                (sample.row_number() + 2 for sample in samples_to_run),
                work_fs_manager,
            ),
            smp_sh.exit_error_function_lines(work_fs_manager, sample_fs_manager),
            map(smp_sh.exit_error, tool_bash_env_wrapper.init_env_lines()),
            map(
                smp_sh.exit_error,
                smp_sh.SpeSmpIDLinesBuilder(
                    smp_fs.samples_tsv(data_fs_manager.root_dir()),
                ).lines(),
            ),
            (
                smp_sh.exit_error(line)
                for line in (smp_sh.write_slurm_job_id(sample_fs_manager),)
            ),
            (smp_sh.exit_error(line) for line in tool_cmd.commands()),
            tool_bash_env_wrapper.close_env_lines(),
        ):
            script_out.write(line + "\n")

        script_out.write(
            smp_sh.write_done_log(work_fs_manager, sample_fs_manager) + "\n",
        )
    return script_path
