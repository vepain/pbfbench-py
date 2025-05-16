"""Tools script logics."""

from __future__ import annotations

import shutil
import stat
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, assert_never

import pbfbench.abc.tool.bash as abc_tool_bash
import pbfbench.abc.tool.environments as abc_tools_envs
import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.bash.items as bash_items
import pbfbench.experiment.bash.items as exp_bash_items
import pbfbench.experiment.config as exp_cfg
import pbfbench.experiment.file_system as exp_fs
import pbfbench.experiment.slurm.status as exp_slurm_status
import pbfbench.samples.bash as smp_sh
import pbfbench.samples.file_system as smp_fs
import pbfbench.slurm.bash as slurm_bash
import pbfbench.slurm.config as slurm_cfg

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


def run_scripts(
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
    samples_to_run: Iterable[smp_fs.RowNumberedItem],
    exp_config: exp_cfg.ConfigWithOptions,
    tool_connector: abc_tool_visitor.ConnectorWithOptions,
) -> Path:
    """Create the run script."""
    work_exp_fs_manager.slurm_log_fs_manager().log_dir().mkdir(
        parents=True,
        exist_ok=True,
    )

    tool_commands = tool_connector.inputs_to_commands(
        exp_config,
        data_exp_fs_manager,
        work_exp_fs_manager,
    )
    tool_bash_env_wrapper = abc_tools_envs.BashEnvWrapper(
        data_exp_fs_manager.tool_env_script_sh(),
    )

    for sub_script_path in (
        _init_env_script(work_exp_fs_manager, tool_bash_env_wrapper),
        _command_script(data_exp_fs_manager, work_exp_fs_manager, tool_commands),
        _close_env_script(work_exp_fs_manager, tool_bash_env_wrapper),
    ):
        _add_x_permissions(sub_script_path)
        _copy_to_data_dir(sub_script_path, data_exp_fs_manager)

    return _sbatch_script(
        work_exp_fs_manager,
        exp_config.slurm_config(),
        samples_to_run,
    )


def _init_env_script(
    work_exp_fs_manager: exp_fs.WorkManager,
    tool_bash_env_wrapper: abc_tools_envs.BashEnvWrapper,
) -> Path:
    """Write the init environment script."""
    script_path = work_exp_fs_manager.scripts_fs_manager().step_script(
        exp_bash_items.Steps.INIT_ENV,
    )
    with script_path.open("w") as f_out:
        for line in tool_bash_env_wrapper.init_env_lines():
            f_out.write(line + "\n")
    return script_path


def _command_script(
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
    tool_cmd: abc_tool_bash._CommandsWithOptions,
) -> Path:
    """Write the command script (which `srun` will call)."""
    script_path = work_exp_fs_manager.scripts_fs_manager().step_script(
        exp_bash_items.Steps.COMMAND,
    )
    with script_path.open("w") as command_out:
        command_out.write(f"{bash_items.BASH_SHEBANG}\n\n")
        for line in CommandLinesBuilder.lines(data_exp_fs_manager, tool_cmd):
            command_out.write(line + "\n")
    return script_path


def _close_env_script(
    work_exp_fs_manager: exp_fs.WorkManager,
    tool_bash_env_wrapper: abc_tools_envs.BashEnvWrapper,
) -> Path:
    """Write the close environment script."""
    script_path = work_exp_fs_manager.scripts_fs_manager().step_script(
        exp_bash_items.Steps.CLOSE_ENV,
    )
    with script_path.open("w") as f_out:
        for line in tool_bash_env_wrapper.close_env_lines():
            f_out.write(line + "\n")
    return script_path


def _add_x_permissions(cmd_sh_path: Path) -> None:
    """Chmod +x the subscript (called by `srun`) for everyone."""
    st = cmd_sh_path.stat()
    cmd_sh_path.chmod(st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _copy_to_data_dir(
    script_path: Path,
    data_exp_fs_manager: exp_fs.DataManager,
) -> None:
    """Copy the script to the data directory."""
    shutil.copy(script_path, data_exp_fs_manager.scripts_fs_manager().scripts_dir())


def _sbatch_script(
    work_exp_fs_manager: exp_fs.WorkManager,
    slurm_config: slurm_cfg.Config,
    samples_to_run: Iterable[smp_fs.RowNumberedItem],
) -> Path:
    """Write the sbatch script."""
    script_path = work_exp_fs_manager.scripts_fs_manager().sbatch_script()
    with script_path.open("w") as sbatch_out:
        for line in SbatchLinesBuilder.lines(
            slurm_config,
            work_exp_fs_manager,
            samples_to_run,
        ):
            sbatch_out.write(line + "\n")
    return script_path


class StepLinesBuilder:
    """Sbatch step lines builder."""

    @classmethod
    def set_step_ok_file(
        cls,
        work_exp_fs_manager: exp_fs.WorkManager,
        step: exp_bash_items.Steps,
    ) -> Iterator[str]:
        """Set step OK file variable."""
        yield bash_items.Variable(
            f"{step}_STEP_OK_FILE",
        ).set(
            bash_items.path_to_str(
                work_exp_fs_manager.slurm_log_fs_manager().script_step_status_file(
                    slurm_bash.SLURM_JOB_ID_FROM_VARS,
                    step,
                    exp_slurm_status.ScriptSteps.OK,
                ),
            ),
        )

    @classmethod
    def step_error_file(
        cls,
        work_exp_fs_manager: exp_fs.WorkManager,
        step: exp_bash_items.Steps,
    ) -> Iterator[str]:
        """Set step error file variable."""
        yield bash_items.Variable(
            f"{step}_STEP_ERROR_FILE",
        ).set(
            bash_items.path_to_str(
                work_exp_fs_manager.slurm_log_fs_manager().script_step_status_file(
                    slurm_bash.SLURM_JOB_ID_FROM_VARS,
                    step,
                    exp_slurm_status.ScriptSteps.ERROR,
                ),
            ),
        )

    @classmethod
    def set_script_path(
        cls,
        work_exp_fs_manager: exp_fs.WorkManager,
        step: exp_bash_items.Steps,
    ) -> Iterator[str]:
        """Set script path variable."""
        yield bash_items.Variable(
            f"{step}_SCRIPT_PATH",
        ).set(
            bash_items.path_to_str(
                work_exp_fs_manager.scripts_fs_manager().step_script(step),
            ),
        )


class SbatchLinesBuilder:
    """Sbatch lines builder."""

    TEMPLATE_SCRIPT = Path(__file__) / "sbatch_template.sh"

    PBFBENCH_DO_PREFIX = "# PBFBENCH_DO:"

    @classmethod
    def lines(
        cls,
        slurm_config: slurm_cfg.Config,
        work_exp_fs_manager: exp_fs.WorkManager,
        samples_to_run: Iterable[smp_fs.RowNumberedItem],
    ) -> Iterator[str]:
        """Return sbatch lines."""
        with cls.TEMPLATE_SCRIPT.open("r") as template_in:
            for line in template_in:
                pbfbench_do = cls._pbfbench_do(line)
                if pbfbench_do is None:
                    yield line.rstrip()
                else:
                    yield from cls._pbfbench_do_lines(
                        line,
                        pbfbench_do,
                        slurm_config,
                        work_exp_fs_manager,
                        samples_to_run,
                    )

    @classmethod
    def _pbfbench_do(cls, line: str) -> exp_bash_items.PbfbenchDo | None:
        """Return the PBFBENCH_DO comment if it is, otherwise None."""
        if line.startswith(cls.PBFBENCH_DO_PREFIX):
            pbfbench_do_str = line[len(cls.PBFBENCH_DO_PREFIX) :].rstrip().split(":")[0]
            return exp_bash_items.PbfbenchDo(pbfbench_do_str)
        return None

    @classmethod
    def _script_step(cls, line: str) -> exp_bash_items.Steps:
        """Return the script step if it is, otherwise None."""
        step_str = line[len(cls.PBFBENCH_DO_PREFIX) :].rstrip().split(":")[1]
        return exp_bash_items.Steps(step_str)

    @classmethod
    def _pbfbench_do_lines(
        cls,
        line: str,
        pbfbench_do: exp_bash_items.PbfbenchDo,
        slurm_config: slurm_cfg.Config,
        work_exp_fs_manager: exp_fs.WorkManager,
        samples_to_run: Iterable[smp_fs.RowNumberedItem],
    ) -> Iterator[str]:
        """Return the lines for the PBFBENCH_DO comment."""
        match pbfbench_do:
            case exp_bash_items.PbfbenchDo.SBATCH_COMMENTS:
                return slurm_bash.SbatchCommentLinesBuilder.lines(
                    slurm_config,
                    (
                        smp_fs.to_line_number_base_one(sample)
                        for sample in samples_to_run
                    ),
                    work_exp_fs_manager,
                )
            case exp_bash_items.PbfbenchDo.ARRAY_JOB_ID_FILE:
                return iter(
                    (
                        bash_items.Variable(pbfbench_do.value).set(
                            bash_items.path_to_str(
                                work_exp_fs_manager.slurm_log_fs_manager()
                                .job_id_file_manager()
                                .path(),
                            ),
                        ),
                    ),
                )
            case exp_bash_items.PbfbenchDo.STEP:
                step = cls._script_step(line)
                return chain(
                    StepLinesBuilder.set_script_path(work_exp_fs_manager, step),
                    StepLinesBuilder.set_step_ok_file(work_exp_fs_manager, step),
                    StepLinesBuilder.step_error_file(work_exp_fs_manager, step),
                )
        assert_never(pbfbench_do)


class CommandLinesBuilder:
    """Command lines builder."""

    @classmethod
    def lines(
        cls,
        data_exp_fs_manager: exp_fs.DataManager,
        tool_cmd: abc_tool_bash._CommandsWithOptions,
    ) -> Iterator[str]:
        """Return command lines."""
        yield bash_items.BASH_SHEBANG
        yield ""
        yield "set -e"
        yield ""
        yield from smp_sh.SpeSmpIDLinesBuilder(
            data_exp_fs_manager.samples_tsv(),
        ).lines()
        yield ""
        yield from tool_cmd.commands()
