"""Slurm module."""

from __future__ import annotations

import logging
import subprocess
from itertools import chain
from typing import TYPE_CHECKING

import pbfbench.bash.items as bash_items
import pbfbench.experiment.file_system as exp_fs
import pbfbench.experiment.slurm.file_system as exp_slurm_fs
import pbfbench.slurm.config as slurm_cfg
import pbfbench.slurm.status as slurm_status
from pbfbench import subprocess_lib

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path

_LOGGER = logging.getLogger(__name__)

SBATCH_CMD = "sbatch"


def array_task_job_id(array_job_id: str, task_job_id: str) -> str:
    """Get array task job id from each job id part."""
    return f"{array_job_id}_{task_job_id}"


SLURM_ARRAY_JOB_ID_VAR = bash_items.Variable("SLURM_ARRAY_JOB_ID")
SLURM_ARRAY_TASK_ID_VAR = bash_items.Variable("SLURM_ARRAY_TASK_ID")
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
        work_exp_fs_manager: exp_fs.WorkManager,
    ) -> Iterator[str]:
        """Iterate over the sbatch comment lines."""
        return (
            f"{cls.COMMENT} {line}"
            for line in chain(
                cls._job_name_lines(work_exp_fs_manager),
                cls._job_array_lines(samples_to_run_indices),
                cls._sbatch_option_log_lines(
                    work_exp_fs_manager.slurm_log_fs_manager(),
                ),
                iter(slurm_config),
            )
        )

    @classmethod
    def _job_name_lines(cls, work_exp_fs_manager: exp_fs.WorkManager) -> Iterator[str]:
        """Iterate over the job name lines."""
        job_name = "_".join(
            [
                work_exp_fs_manager.tool_description().topic().name(),
                work_exp_fs_manager.tool_description().name(),
                work_exp_fs_manager.experiment_name(),
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
    def _sbatch_option_log_lines(
        cls,
        logs_manager: exp_slurm_fs.LogsManager,
    ) -> Iterator[str]:
        """Iterate over the sbatch log option lines."""
        yield f"--output={logs_manager.stdout(cls.JOB_ID)}"
        yield f"--error={logs_manager.stderr(cls.JOB_ID)}"


SACCT_CMD = "sacct"
BASH_CMD = "bash"


def write_slurm_stats(job_id: str, psv_path: Path) -> None:
    """Write sbatch stats."""
    sacct_cmd = f"{SACCT_CMD} --long --jobs {job_id} --parsable2 > {psv_path}"

    cmd_path = subprocess_lib.command_path(BASH_CMD)
    result = subprocess.run(  # noqa: S603
        [str(x) for x in [cmd_path, "-c", f"'{sacct_cmd}'"]],
        capture_output=True,
        text=True,
        check=False,
    )
    _LOGGER.debug("%s stdout: %s", SACCT_CMD, result.stdout)
    _LOGGER.debug("%s stderr: %s", SACCT_CMD, result.stderr)


def get_states(job_ids: Iterable[str]) -> dict[str, slurm_status.SACCTState]:
    """Get jobs states."""
    cmd_path = subprocess_lib.command_path(SACCT_CMD)
    result = subprocess.run(  # noqa: S602
        f"{cmd_path} --jobs " + ",".join(job_ids) + " --format=JobID,State -P -X",
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )
    job_states: dict[str, slurm_status.SACCTState] = {}
    for stdout_line in result.stdout.splitlines()[1:]:
        columns = stdout_line.split("|")
        job_states[columns[0]] = slurm_status.SACCTState(columns[1])
    return job_states
