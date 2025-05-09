"""Slurm module."""

from __future__ import annotations

import logging
import subprocess
from itertools import chain
from typing import TYPE_CHECKING

import pbfbench.experiment.file_system as exp_fs
import pbfbench.shell as sh
import pbfbench.slurm.config as slurm_cfg
from pbfbench import subprocess_lib

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path

_LOGGER = logging.getLogger(__name__)

SBATCH_CMD = "sbatch"


def array_task_job_id(array_job_id: str, task_job_id: str) -> str:
    """Get array task job id from each job id part."""
    return f"{array_job_id}_{task_job_id}"


SLURM_ARRAY_JOB_ID_VAR = sh.Variable("SLURM_ARRAY_JOB_ID")
SLURM_ARRAY_TASK_ID_VAR = sh.Variable("SLURM_ARRAY_TASK_ID")
SLURM_JOB_ID_FROM_VARS = array_task_job_id(
    SLURM_ARRAY_JOB_ID_VAR.eval(),
    SLURM_ARRAY_TASK_ID_VAR.eval(),
)


class SbatchCommentLinesBuilder:
    """Sbatch comment lines builder."""

    COMMENT = "#SBATCH"

    ARRAY_JOB_ID = "%A"
    TASK_JOB_ID = "%a"
    JOB_ID = array_task_job_id(ARRAY_JOB_ID, TASK_JOB_ID)

    @classmethod
    def lines(
        cls,
        slurm_config: slurm_cfg.Config,
        samples_to_run_indices: Iterable[int],
        work_fs_manager: exp_fs.Manager,
    ) -> Iterator[str]:
        """Iterate over the sbatch comment lines."""
        return (
            f"{cls.COMMENT} {line}"
            for line in chain(
                cls._job_name_lines(work_fs_manager),
                iter(slurm_config),
                cls._job_array_lines(samples_to_run_indices),
                cls._sbatch_option_log_lines(work_fs_manager),
            )
        )

    @classmethod
    def _job_name_lines(cls, work_fs_manager: exp_fs.Manager) -> Iterator[str]:
        """Iterate over the job name lines."""
        job_name = "_".join(
            [
                work_fs_manager.tool_description().topic().name(),
                work_fs_manager.tool_description().name(),
                work_fs_manager.experiment_name(),
            ],
        )
        yield f"--job-name={job_name}"

    @classmethod
    def _job_array_lines(cls, samples_to_run_indices: Iterable[int]) -> Iterator[str]:
        """Iterate over the job array comment lines."""
        array_job_str = "--array=" + ",".join(
            str(sample_index) for sample_index in samples_to_run_indices
        )
        yield array_job_str

    @classmethod
    def _sbatch_option_log_lines(cls, work_fs_manager: exp_fs.Manager) -> Iterator[str]:
        """Iterate over the sbatch log option lines."""
        yield f"--output={work_fs_manager.sbatch_out_file(cls.JOB_ID)}"
        yield f"--error={work_fs_manager.sbatch_err_file(cls.JOB_ID)}"


class ExitFunctionLinesBuilder:
    """Exit function lines builder."""

    EXIT_INIT_ENV_ERROR_FN_NAME = "exit_init_env_error"
    EXIT_COMMAND_ERROR_FN_NAME = "exit_command_error"
    EXIT_CLOSE_ENV_ERROR_FN_NAME = "exit_close_env_error"
    EXIT_END_FN_NAME = "exit_end"

    @classmethod
    def lines(cls, work_fs_manager: exp_fs.Manager) -> Iterator[str]:
        """Iterate over bash lines defining the exit functions."""
        yield from chain(
            cls._err_fn_lines(
                cls.EXIT_INIT_ENV_ERROR_FN_NAME,
                work_fs_manager.sbatch_init_env_error_file(SLURM_JOB_ID_FROM_VARS),
            ),
            cls._err_fn_lines(
                cls.EXIT_COMMAND_ERROR_FN_NAME,
                work_fs_manager.sbatch_command_error_file(SLURM_JOB_ID_FROM_VARS),
            ),
            cls._err_fn_lines(
                cls.EXIT_CLOSE_ENV_ERROR_FN_NAME,
                work_fs_manager.sbatch_close_env_error_file(SLURM_JOB_ID_FROM_VARS),
            ),
            cls._ok_fn_lines(
                cls.EXIT_END_FN_NAME,
                work_fs_manager.sbatch_end_file(SLURM_JOB_ID_FROM_VARS),
            ),
        )

    @classmethod
    def _function_lines(
        cls,
        fn_name: str,
        status_file: Path,
        code: int,
    ) -> Iterator[str]:
        yield f"function {fn_name}" + " {"
        yield f"  touch {status_file}"
        yield f"  exit {code}"
        yield "}"

    @classmethod
    def _ok_fn_lines(cls, fn_name: str, status_file: Path) -> Iterator[str]:
        yield from cls._function_lines(fn_name, status_file, 0)

    @classmethod
    def _err_fn_lines(cls, fn_name: str, status_file: Path) -> Iterator[str]:
        yield from cls._function_lines(fn_name, status_file, 1)


SACCT_CMD = "sacct"
BASH_CMD = "bash"


def write_slurm_stats(job_id: str, psv_path: Path) -> None:
    """Write sbatch stats."""
    tmp_bash_script_path = psv_path.with_suffix(".sh")

    with tmp_bash_script_path.open("w") as f:
        f.write(sh.BASH_SHEBANG + "\n")
        f.write(f"{SACCT_CMD} --long --jobs {job_id} --parsable2 > {psv_path}")

    cmd_path = subprocess_lib.command_path(BASH_CMD)
    result = subprocess.run(  # noqa: S603
        [str(x) for x in [cmd_path, tmp_bash_script_path]],
        capture_output=True,
        check=False,
    )
    _LOGGER.debug("sbath stdout: %s", result.stdout)
    _LOGGER.debug("sbath stderr: %s", result.stderr)

    tmp_bash_script_path.unlink()
