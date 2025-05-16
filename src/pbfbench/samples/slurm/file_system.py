"""Sample slurm file system manager."""

from __future__ import annotations

from pathlib import Path

import pbfbench.samples.slurm.status as smp_slurm_status
import pbfbench.slurm.status as slurm_status


class Manager:
    """Sample slurm file system manager."""

    STATS_PSV_NAME = Path("stats.psv")
    STDOUT_LOG_NAME = Path("stdout.log")
    STDERR_LOG_NAME = Path("stderr.log")

    def __init__(self, slurm_directory: Path) -> None:
        """Initialize."""
        self.__slurm_dir = slurm_directory
        self.__command_steps_status_file_manager = CommandStepStatusFileManager(
            self.__slurm_dir,
        )
        self.__job_state_file_builder = JobStateFileManager(self.__slurm_dir)

    def slurm_dir(self) -> Path:
        """Get slurm sample directory path."""
        return self.__slurm_dir

    def command_steps_status_file_manager(self) -> CommandStepStatusFileManager:
        """Get command steps status file manager."""
        return self.__command_steps_status_file_manager

    def stats_psv(self) -> Path:
        """Get stats file path."""
        return self.__slurm_dir / self.STATS_PSV_NAME

    def stdout_log(self) -> Path:
        """Get stdout file path."""
        return self.__slurm_dir / self.STDOUT_LOG_NAME

    def stderr_log(self) -> Path:
        """Get stderr file path."""
        return self.__slurm_dir / self.STDERR_LOG_NAME

    def job_state_file_builder(self) -> JobStateFileManager:
        """Get job state file builder."""
        return self.__job_state_file_builder


class CommandStepStatusFileManager:
    """Command step status file manager."""

    YAML_NAME = "command_steps_status.yaml"

    def __init__(self, directory: Path) -> None:
        """Initialize."""
        self.__directory = directory

    def path(self) -> Path:
        """Get command step status file."""
        return self.__directory / self.YAML_NAME

    def get_command_step_status(self) -> smp_slurm_status.CommandStepsProcess:
        """Get command step status."""
        return smp_slurm_status.CommandStepsProcess.from_yaml(self.path())


class JobStateFileManager:
    """Job state file builder."""

    PREFIX = "job_state"

    @classmethod
    def filename(cls, sacct_state: slurm_status.SACCTState) -> Path:
        """Build job state file."""
        return Path(f"{cls.PREFIX}.{sacct_state}")

    def __init__(self, directory: Path) -> None:
        """Initialize."""
        self.__directory = directory

    def path(self, sacct_state: slurm_status.SACCTState) -> Path:
        """Get job state file."""
        return self.__directory / self.filename(sacct_state)

    def find_path(self) -> Path:
        """Get job state file.

        Raises
        ------
        FileNotFoundError
            If job state file is not found.
        """
        path = next(
            (
                file
                for file in self.__directory.iterdir()
                if file.name.startswith(self.PREFIX)
            ),
            None,
        )
        if path is None:
            _error_msg = f"Job state file not found in {self.__directory}"
            raise FileNotFoundError(_error_msg)

        return path

    def extract_sacct_state(self) -> slurm_status.SACCTState:
        """Get job state."""
        return slurm_status.SACCTState(self.find_path().suffix)
