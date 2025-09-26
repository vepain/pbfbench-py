"""Experiment history logic."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Self, final

import pbfbench.samples.status as smp_status
from pbfbench.yaml_interface import YAMLInterface

from . import in_progress, monitors
from . import managers as exp_managers


@final
class RunStats(YAMLInterface):
    """Stats of an experiment run."""

    KEY_TOTAL_NUMBER_OF_SAMPLES = "total_number_of_samples"
    KEY_NUMBER_OF_SUCCESSFUL_SAMPLES = "number_of_successful_samples"
    KEY_NUMBER_OF_SAMPLES_WITH_MISSING_INPUTS = "number_of_samples_with_missing_inputs"
    KEY_NUMBER_OF_FAILED_SAMPLES = "number_of_failed_samples"
    KEY_NUMBER_OF_NOT_RUN_SAMPLES = "number_of_not_run_samples"

    @classmethod
    def from_status_map(cls, status_map: Callable[[smp_status.Status], int]) -> Self:
        """Convert status map to stats."""
        return cls(
            status_map(smp_status.OK.OK),
            status_map(smp_status.Error.MISSING_INPUTS),
            status_map(smp_status.Error.ERROR),
            status_map(smp_status.Error.NOT_RUN),
        )

    @classmethod
    def from_yaml_load(cls, pyyaml_obj: dict[str, int]) -> Self:
        """Convert dict to object."""
        return cls(
            int(pyyaml_obj[cls.KEY_NUMBER_OF_SUCCESSFUL_SAMPLES]),
            int(pyyaml_obj[cls.KEY_NUMBER_OF_SAMPLES_WITH_MISSING_INPUTS]),
            int(pyyaml_obj[cls.KEY_NUMBER_OF_FAILED_SAMPLES]),
            int(pyyaml_obj[cls.KEY_NUMBER_OF_NOT_RUN_SAMPLES]),
        )

    def __init__(
        self,
        number_of_successful_samples: int,
        number_of_samples_with_missing_inputs: int,
        number_of_failed_samples: int,
        number_of_not_run_samples: int,
    ) -> None:
        self._number_of_successful_samples = number_of_successful_samples
        self._number_of_samples_with_missing_inputs = (
            number_of_samples_with_missing_inputs
        )
        self._number_of_failed_samples = number_of_failed_samples
        self._number_of_not_run_samples = number_of_not_run_samples

    def total_number_of_samples(self) -> int:
        """Get total number of samples."""
        return (
            self._number_of_successful_samples
            + self._number_of_samples_with_missing_inputs
            + self._number_of_failed_samples
            + self._number_of_not_run_samples
        )

    def number_of_successful_samples(self) -> int:
        """Get number of successful samples."""
        return self._number_of_successful_samples

    def number_of_samples_with_missing_inputs(self) -> int:
        """Get number of samples with missing inputs."""
        return self._number_of_samples_with_missing_inputs

    def number_of_failed_samples(self) -> int:
        """Get number of failed samples."""
        return self._number_of_failed_samples

    def number_of_not_run_samples(self) -> int:
        """Get number of not run samples."""
        return self._number_of_not_run_samples

    def to_yaml_dump(self) -> dict[str, int]:
        """Convert to dict."""
        return {
            self.KEY_TOTAL_NUMBER_OF_SAMPLES: self.total_number_of_samples(),
            self.KEY_NUMBER_OF_SUCCESSFUL_SAMPLES: self._number_of_successful_samples,
            self.KEY_NUMBER_OF_SAMPLES_WITH_MISSING_INPUTS: (
                self._number_of_samples_with_missing_inputs
            ),
            self.KEY_NUMBER_OF_FAILED_SAMPLES: self._number_of_failed_samples,
            self.KEY_NUMBER_OF_NOT_RUN_SAMPLES: self._number_of_not_run_samples,
        }


@final
class Event(YAMLInterface):
    """Base class for event logics."""

    KEY_DATE = "date"
    KEY_JOB_ID = "job_id"
    KEY_STATS = "stats"

    @classmethod
    def from_yaml_load(cls, obj_dict: dict[str, Any]) -> Self:
        """Convert dict to object."""
        return cls(
            obj_dict[cls.KEY_DATE],
            obj_dict.get(cls.KEY_JOB_ID),
            RunStats.from_yaml_load(obj_dict[cls.KEY_STATS]),
        )

    def __init__(self, date: str, job_id: str | None, stats: RunStats) -> None:
        self._date = date
        self._job_id = job_id
        self._stats = stats

    def date(self) -> str:
        """Get date."""
        return self._date

    def job_id(self) -> str | None:
        """Get job id."""
        return self._job_id

    def stats(self) -> RunStats:
        """Get stats."""
        return self._stats

    def to_yaml_dump(self) -> dict[str, Any]:
        """Convert to dict."""
        return {
            self.KEY_DATE: self._date,
            self.KEY_JOB_ID: self._job_id,
            self.KEY_STATS: self._stats.to_yaml_dump(),
        }


@final
class History(list[Event], YAMLInterface):
    """Experiment run history."""

    @classmethod
    def from_yaml_load(cls, obj_list: list[dict[str, Any]]) -> Self:
        """Convert list to object."""
        return cls(
            [Event.from_yaml_load(event_dict) for event_dict in obj_list],
        )

    def to_yaml_dump(self) -> list[dict[str, Any]]:
        """Convert to dict."""
        return [event.to_yaml_dump() for event in self]


def update_history(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> None:
    """Update history."""
    event = Event(*_date_and_job_id(exp_manager), _stats_from_monitors(exp_manager))

    _add_event_to_history_yaml(exp_manager, event)


def _date_and_job_id(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> tuple[str, str | None]:
    if exp_manager.work_fs_manager().in_progress_yaml().exists():
        in_progress_metadata = in_progress.InWorkingDirectory.from_yaml(
            exp_manager.work_fs_manager().in_progress_yaml(),
        )
        return in_progress_metadata.date(), in_progress_metadata.job_id()
    return in_progress.get_today_format_string(), None


def _stats_from_monitors(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> RunStats:
    number_of_status: dict[smp_status.Status, int] = {
        smp_status.OK.OK: 0,
        smp_status.Error.MISSING_INPUTS: 0,
        smp_status.Error.ERROR: 0,
        smp_status.Error.NOT_RUN: 0,
    }
    for resolved_sample in monitors.iter_resolved_samples(
        exp_manager.work_fs_manager(),
    ):
        number_of_status[resolved_sample.status()] += 1

    number_of_status[smp_status.Error.NOT_RUN] = sum(
        1 for _ in monitors.iter_unresolved_samples(exp_manager.work_fs_manager())
    )

    return RunStats.from_status_map(lambda s: number_of_status[s])


def _add_event_to_history_yaml(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    event: Event,
) -> None:
    if exp_manager.data_fs_manager().history_yaml().exists():
        history = History.from_yaml(exp_manager.data_fs_manager().history_yaml())
    else:
        history = History()
    history.append(event)
    history.to_yaml(exp_manager.data_fs_manager().history_yaml())
