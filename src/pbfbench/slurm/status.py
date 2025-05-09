"""Slurm status logics."""

from enum import StrEnum

import pbfbench.experiment.file_system as exp_fs


class Status(StrEnum):
    """Slurm status."""

    INIT_ENV_ERROR = "init_env_error"
    COMMAND_ERROR = "command_error"
    CLOSE_ENV_ERROR = "close_env_error"
    END = "end"


def get_status(work_fs_manager: exp_fs.Manager, job_id: str) -> Status | None:
    """Get sample experiment status."""
    if work_fs_manager.sbatch_init_env_error_file(job_id).exists():
        return Status.INIT_ENV_ERROR
    if work_fs_manager.sbatch_command_error_file(job_id).exists():
        return Status.COMMAND_ERROR
    if work_fs_manager.sbatch_close_env_error_file(job_id).exists():
        return Status.CLOSE_ENV_ERROR
    if work_fs_manager.sbatch_end_file(job_id).exists():
        return Status.END
    return None
