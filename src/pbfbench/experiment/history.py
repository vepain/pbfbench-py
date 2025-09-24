"""Experiment history logic."""

from __future__ import annotations

from typing import Any, Self

from pbfbench.yaml_interface import YAMLInterface


class RunStats(YAMLInterface):
    """Stats of an experiment run."""

    # REFACTOR perhaps RunStats will move

    KEY_NUMBER_OF_SAMPLES = "number_of_samples"
    KEY_NUMBER_OF_SUCCESSFUL_SAMPLES = "number_of_successful_samples"
    KEY_NUMBER_OF_SAMPLES_WITH_MISSING_INPUTS = "number_of_samples_with_missing_inputs"
    KEY_NUMBER_OF_FAILED_SAMPLES = "number_of_failed_samples"

    def __init__(
        self,
        number_of_samples: int,
        number_of_successful_samples: int,
        number_of_samples_with_missing_inputs: int,
        number_of_failed_samples: int,
    ) -> None:
        self._number_of_samples = number_of_samples
        self._number_of_successful_samples = number_of_successful_samples
        self._number_of_samples_with_missing_inputs = (
            number_of_samples_with_missing_inputs
        )
        self._number_of_failed_samples = number_of_failed_samples

    def number_of_samples(self) -> int:
        """Get number of samples."""
        return self._number_of_samples

    def number_of_successful_samples(self) -> int:
        """Get number of successful samples."""
        return self._number_of_successful_samples

    def number_of_samples_with_missing_inputs(self) -> int:
        """Get number of samples with missing inputs."""
        return self._number_of_samples_with_missing_inputs

    def number_of_failed_samples(self) -> int:
        """Get number of failed samples."""
        return self._number_of_failed_samples


class Event(YAMLInterface):
    """Base class for event logics."""

    KEY_DATE = "date"
    KEY_JOB_ID = "job_id"
    KEY_STATS = "stats"

    def __init__(self, date: str, job_id: str, stats: RunStats) -> None:
        self._date = date
        self._job_id = job_id
        self._stats = stats

    def date(self) -> str:
        """Get date."""
        return self._date

    def job_id(self) -> str:
        """Get job id."""
        return self._job_id

    def stats(self) -> RunStats:
        """Get stats."""
        return self._stats


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
