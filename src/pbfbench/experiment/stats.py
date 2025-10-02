"""Experiment stats module."""

from __future__ import annotations

from typing import Self, final

import pbfbench.samples.status as smp_status
from pbfbench.yaml_interface import YAMLInterface


@final
class Samples(YAMLInterface):
    """Stats of samples for an experiment."""

    KEY_TOTAL_NUMBER_OF_SAMPLES = "total_number_of_samples"
    KEY_NUMBER_OF_SUCCESSFUL_SAMPLES = "number_of_successful_samples"
    KEY_NUMBER_OF_SAMPLES_WITH_MISSING_INPUTS = "number_of_samples_with_missing_inputs"
    KEY_NUMBER_OF_FAILED_SAMPLES = "number_of_failed_samples"
    KEY_NUMBER_OF_NOT_RUN_SAMPLES = "number_of_not_run_samples"

    @classmethod
    def from_status_map(cls, status_map: smp_status.StatusMap[int]) -> Self:
        """Convert status map to stats."""
        return cls(
            status_map[smp_status.OK.OK],
            status_map[smp_status.Error.MISSING_INPUTS],
            status_map[smp_status.Error.ERROR],
            status_map[smp_status.Error.NOT_RUN],
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
