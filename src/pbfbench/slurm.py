"""Slurm module."""

from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, Self

import pbfbench.experiment.file_system as exp_fs
import pbfbench.shell as sh
from pbfbench import subprocess_lib
from pbfbench.yaml_interface import YAMLInterface

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path

SBATCH_CMD = "sbatch"

SBATCH_COMMENT = "#SBATCH"

SLURM_ARRAY_JOB_ID_VAR = sh.Variable("SLURM_ARRAY_JOB_ID")
SLURM_ARRAY_TASK_ID_VAR = sh.Variable("SLURM_ARRAY_TASK_ID")


class Config(list[str], YAMLInterface):
    """Slurm config."""

    @classmethod
    def from_yaml_load(cls, pyyaml_obj: list[str]) -> Self:
        """Convert pyyaml object to self."""
        return cls(iter(pyyaml_obj))

    def to_yaml_dump(self) -> list[str]:
        """Convert to list."""
        return list(self)


def comment_lines(
    slurm_config: Config,
    samples_to_run_indices: Iterable[int],
    work_fs_manager: exp_fs.Manager,
) -> Iterator[str]:
    """Iterate over the slurm comment lines."""
    return chain(
        job_name_lines(work_fs_manager),
        iter(slurm_config),
        job_array_lines(samples_to_run_indices),
        log_lines(work_fs_manager),
    )


def job_name_lines(work_fs_manager: exp_fs.Manager) -> Iterator[str]:
    """Iterate over the job name lines."""
    job_name = "_".join(
        [
            work_fs_manager.tool_description().topic().name(),
            work_fs_manager.tool_description().name(),
            work_fs_manager.experiment_name(),
        ],
    )
    yield f"{SBATCH_COMMENT} --job-name={job_name}"


def job_array_lines(samples_to_run_indices: Iterable[int]) -> Iterator[str]:
    """Iterate over the job array comment lines."""
    array_job_str = f"{SBATCH_COMMENT} --array=" + ",".join(
        str(sample_index) for sample_index in samples_to_run_indices
    )
    yield array_job_str


PREFIX_SLURM_LOG = "slurm"
JOB_ID_VARIABLE = "%A_%a"
OUT_EXTENSION = "out"
ERR_EXTENSION = "err"


def out_log_path(work_fs_manager: exp_fs.Manager, job_id: str) -> Path:
    """Get slurm log path."""
    return (
        work_fs_manager.tmp_slurm_logs_dir()
        / f"{PREFIX_SLURM_LOG}_{job_id}.{OUT_EXTENSION}"
    )


def out_log_var_path(work_fs_manager: exp_fs.Manager) -> Path:
    """Get slurm log variable path."""
    return out_log_path(work_fs_manager, JOB_ID_VARIABLE)


def err_log_path(work_fs_manager: exp_fs.Manager, job_id: str) -> Path:
    """Get slurm log path."""
    return (
        work_fs_manager.tmp_slurm_logs_dir()
        / f"{PREFIX_SLURM_LOG}_{job_id}.{ERR_EXTENSION}"
    )


def err_log_var_path(work_fs_manager: exp_fs.Manager) -> Path:
    """Get slurm log variable path."""
    return err_log_path(work_fs_manager, JOB_ID_VARIABLE)


def log_lines(work_fs_manager: exp_fs.Manager) -> Iterator[str]:
    """Iterate over the slurm log lines."""
    yield f"{SBATCH_COMMENT} --output={out_log_var_path(work_fs_manager)}"
    yield f"{SBATCH_COMMENT} --error={err_log_var_path(work_fs_manager)}"


SACCT_CMD = "sacct"


def write_slurm_stats(job_id: str, psv_path: Path) -> None:
    """Write sbatch stats."""
    cmd_path = subprocess_lib.command_path(SACCT_CMD)
    cli_line = [cmd_path, "--long", "--jobs", job_id, "--parsable2", ">", psv_path]
    subprocess_lib.run_cmd(cli_line, SACCT_CMD)
