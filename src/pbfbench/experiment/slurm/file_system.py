"""Slurm file manager."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import pbfbench.experiment.bash.items as exp_bash_items
import pbfbench.experiment.slurm.status as exp_slurm_status


# REFACTOR not so clear, follow work dir structure for py module(?)
class LogsManager:
    """Slurm logs manager."""

    def __init__(self, log_directory: Path) -> None:
        """Initialize."""
        self.__log_directory = log_directory
        self.__job_id_file_manager = JobIDFileManager(self.__log_directory)

    def log_dir(self) -> Path:
        """Get log directory."""
        return self.__log_directory

    def job_id_file_manager(self) -> JobIDFileManager:
        """Get array job id file manager."""
        return self.__job_id_file_manager

    def stdout(self, job_id: str) -> Path:
        """Get sbatch out file."""
        return self.log_dir() / SlurmLogFilesBuilder.io_stream(
            job_id,
            SlurmLogFilesBuilder.IOStreams.STDOUT,
        )

    def stderr(self, job_id: str) -> Path:
        """Get sbatch err file."""
        return self.log_dir() / SlurmLogFilesBuilder.io_stream(
            job_id,
            SlurmLogFilesBuilder.IOStreams.STDERR,
        )

    def script_step_status_file(
        self,
        job_id: str,
        step: exp_bash_items.Steps,
        status: exp_slurm_status.ScriptSteps,
    ) -> Path:
        """Get bash step status file."""
        return self.log_dir() / ScriptStepStatusFilesBuilder.script_step(
            job_id,
            step,
            status,
        )

    # REFACTOR rename CommandStep by ScriptStep


class JobIDFileManager:
    """Array job ID file manager."""

    # File containing the job ID (equals to %A or SLURM_ARRAY_JOB_ID)
    ARRAY_JOB_ID_FILENAME = Path("array_job.id")

    def __init__(self, log_directory: Path) -> None:
        """Initialize."""
        self.__log_directory = log_directory

    def path(self) -> Path:
        """Get array job ID file path."""
        return self.__log_directory / self.ARRAY_JOB_ID_FILENAME

    def get_job_id(self) -> str:
        """Get array job ID."""
        return self.path().read_text().strip()


class SlurmLogFilesBuilder:
    """Slurm logs files builder."""

    class IOStreams(StrEnum):
        """IO streams."""

        STDOUT = "stdout"
        STDERR = "stderr"

    LOG_EXT = "log"

    @classmethod
    def io_stream(cls, job_id: str, stream: IOStreams) -> Path:
        """Get IO stream filename."""
        return Path(f"{job_id}_{stream}.{cls.LOG_EXT}")


class ScriptStepStatusFilesBuilder:
    """Script step status files builder."""

    # REFACTOR use common part with scripts
    class CommandStepsPrefix(StrEnum):
        """Command steps."""

        INIT_ENV = "init_env"
        COMMAND = "command"
        CLOSE_ENV = "close_env"

        @classmethod
        def from_step(
            cls,
            step: exp_bash_items.Steps,
        ) -> ScriptStepStatusFilesBuilder.CommandStepsPrefix:
            """Convert bash step to command step prefix."""
            match step:
                case exp_bash_items.Steps.INIT_ENV:
                    return cls.INIT_ENV
                case exp_bash_items.Steps.COMMAND:
                    return cls.COMMAND
                case exp_bash_items.Steps.CLOSE_ENV:
                    return cls.CLOSE_ENV

    class CommandStepsExt(StrEnum):
        """Command steps."""

        OK = "ok"
        ERROR = "error"

        @classmethod
        def from_status(
            cls,
            status: exp_slurm_status.ScriptSteps,
        ) -> ScriptStepStatusFilesBuilder.CommandStepsExt:
            """Convert command step status to command step ext."""
            match status:
                case exp_slurm_status.ScriptSteps.OK:
                    return cls.OK
                case exp_slurm_status.ScriptSteps.ERROR:
                    return cls.ERROR
                case exp_slurm_status.ScriptSteps.NULL:
                    raise ValueError

    @classmethod
    def script_step(
        cls,
        job_id: str,
        step: exp_bash_items.Steps,
        step_status: exp_slurm_status.ScriptSteps,
    ) -> Path:
        """Get command step status filename."""
        return Path(
            f"{job_id}_{cls.CommandStepsPrefix.from_step(step)}.{cls.CommandStepsExt.from_status(step_status)}",
        )
