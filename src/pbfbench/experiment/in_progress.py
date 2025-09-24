"""In progress experiment logics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self, final

from pbfbench.yaml_interface import YAMLInterface


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
