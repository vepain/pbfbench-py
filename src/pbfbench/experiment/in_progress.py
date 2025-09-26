"""In progress experiment logics."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self, final

from pbfbench.yaml_interface import YAMLInterface

from . import file_system as exp_fs
from . import managers as exp_managers
from .bash import manager as bash_manager


class Base(YAMLInterface, ABC):
    """Base class for in progress metadata."""

    KEY_DATE = "date"
    KEY_JOB_ID = "job_id"

    @classmethod
    @abstractmethod
    def root_directory_key(cls) -> str:
        """Get root directory key."""
        raise NotImplementedError

    @classmethod
    def from_yaml_load(cls, obj_dict: dict[str, Any]) -> Self:
        """Convert dict to object."""
        return cls(
            obj_dict[cls.KEY_DATE],
            Path(obj_dict[cls.root_directory_key()]),
            obj_dict[cls.KEY_JOB_ID],
        )

    def __init__(
        self,
        date: str,
        twin_root_directory: Path,
        job_id: str,
    ) -> None:
        self._date = date
        self._twin_root_directory = twin_root_directory
        self._job_id = job_id

    def date(self) -> str:
        """Get date."""
        return self._date

    def twin_root_directory(self) -> Path:
        """Get twin root directory."""
        return self._twin_root_directory

    def job_id(self) -> str:
        """Get job id."""
        return self._job_id

    def to_yaml_dump(self) -> dict[str, Any]:
        """Convert to dict."""
        return {
            self.KEY_DATE: self._date,
            self.root_directory_key(): self._twin_root_directory,
            self.KEY_JOB_ID: self._job_id,
        }


@final
class InDataDirectory(Base):
    """In data experiment metadata."""

    @classmethod
    def root_directory_key(cls) -> str:
        """Get root directory key."""
        return "working_directory"

    def working_directory(self) -> Path:
        """Get working directory."""
        return self._twin_root_directory


@final
class InWorkingDirectory(Base):
    """In working experiment metadata."""

    @classmethod
    def root_directory_key(cls) -> str:
        """Get root directory key."""
        return "data_directory"

    def data_directory(self) -> Path:
        """Get data directory."""
        return self._twin_root_directory


def get_today_format_string() -> str:
    """Get date format string."""
    return datetime.now(tz=UTC).strftime("%Y-%m-%d_%H-%M-%S")


def write_in_progress_metadata(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    sh_manager: bash_manager.Manager,
) -> None:
    """Write in progress metadata."""
    job_id = _get_array_job_id(exp_manager.work_fs_manager())

    data_in_progress = InDataDirectory(
        sh_manager.date_str(),
        exp_manager.work_fs_manager().root_dir(),
        job_id,
    )
    work_in_progress = InWorkingDirectory(
        sh_manager.date_str(),
        exp_manager.data_fs_manager().root_dir(),
        job_id,
    )

    data_in_progress.to_yaml(exp_manager.work_fs_manager().in_progress_yaml())
    work_in_progress.to_yaml(exp_manager.work_fs_manager().in_progress_yaml())


def _get_array_job_id(work_exp_fs_manager: exp_fs.WorkManager) -> str:
    """Wait the tmp array job id file is created and extract the array job id."""
    tmp_job_id_file = (
        work_exp_fs_manager.slurm_log_fs_manager().job_id_file_manager().path()
    )
    while not tmp_job_id_file.exists():
        time.sleep(5)

    job_id = (
        work_exp_fs_manager.slurm_log_fs_manager().job_id_file_manager().get_job_id()
    )
    tmp_job_id_file.unlink()
    return job_id
