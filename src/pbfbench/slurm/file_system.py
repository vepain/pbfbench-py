"""Slurm file manager."""

from pathlib import Path


class LogFiles:
    """Sbatch logs files."""

    PREFIX = "slurm_"

    OUT_EXT = "out"
    ERR_EXT = "err"

    INIT_ENV_ERR_EXT = "init_env_error"
    COMMAND_ERR_EXT = "command_error"
    CLOSE_ENV_ERR_EXT = "close_env_error"
    END_EXT = "end"

    # Correspond to %A or SLURM_ARRAY_JOB_ID
    ARRAY_JOB_ID_FILENAME = Path("array_job.id")

    @classmethod
    def filename_builder(cls, job_id: str, ext: str) -> Path:
        """Filename builder."""
        return Path(f"{cls.PREFIX}{job_id}.{ext}")

    @classmethod
    def out_filename(cls, job_id: str) -> Path:
        """Get sbatch out filename."""
        return cls.filename_builder(job_id, cls.OUT_EXT)

    @classmethod
    def err_filename(cls, job_id: str) -> Path:
        """Get sbatch err filename."""
        return cls.filename_builder(job_id, cls.ERR_EXT)

    @classmethod
    def init_env_error_filename(cls, job_id: str) -> Path:
        """Get sbatch init env error filename."""
        return cls.filename_builder(job_id, cls.INIT_ENV_ERR_EXT)

    @classmethod
    def command_error_filename(cls, job_id: str) -> Path:
        """Get sbatch command error filename."""
        return cls.filename_builder(job_id, cls.COMMAND_ERR_EXT)

    @classmethod
    def close_env_error_filename(cls, job_id: str) -> Path:
        """Get sbatch close env error filename."""
        return cls.filename_builder(job_id, cls.CLOSE_ENV_ERR_EXT)

    @classmethod
    def end_filename(cls, job_id: str) -> Path:
        """Get sbatch end filename."""
        return cls.filename_builder(job_id, cls.END_EXT)
