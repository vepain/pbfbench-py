"""Experiment history logic."""

from __future__ import annotations

from typing import Any, Self, final

import pbfbench.samples.status as smp_status
from pbfbench.yaml_interface import YAMLInterface

from . import in_progress, monitors, stats
from . import managers as exp_managers


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
            stats.Samples.from_yaml_load(obj_dict[cls.KEY_STATS]),
        )

    def __init__(self, date: str, job_id: str | None, stats: stats.Samples) -> None:
        self._date = date
        self._job_id = job_id
        self._stats = stats

    def date(self) -> str:
        """Get date."""
        return self._date

    def job_id(self) -> str | None:
        """Get job id."""
        return self._job_id

    def stats(self) -> stats.Samples:
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
) -> Event:
    """Update history."""
    event = Event(*_date_and_job_id(exp_manager), _stats_from_monitors(exp_manager))
    _add_event_to_history_yaml(exp_manager, event)
    return event


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
) -> stats.Samples:
    number_of_status = smp_status.StatusMap.default(0)
    for resolved_sample in monitors.iter_resolved_samples(
        exp_manager.work_fs_manager(),
    ):
        number_of_status[resolved_sample.status()] += 1

    number_of_status[smp_status.Error.NOT_RUN] = sum(
        1 for _ in monitors.iter_unresolved_samples(exp_manager.work_fs_manager())
    )

    return stats.Samples.from_status_map(number_of_status)


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
