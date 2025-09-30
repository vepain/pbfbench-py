"""Experiment stats module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.items as smp_items

if TYPE_CHECKING:
    from collections.abc import Iterable


class RunStatsWithOptions:
    """Experiment run stats for tools with options."""

    @classmethod
    def new(cls, data_exp_fs_manager: exp_fs.DataManager) -> Self:
        """Create new run stats."""
        with smp_fs.TSVReader.open(data_exp_fs_manager.samples_tsv()) as smp_tsv_in:
            number_of_samples = sum(1 for _ in smp_tsv_in.iter_row_numbered_items())
        return cls(number_of_samples, 0, None)

    def __init__(
        self,
        number_of_samples: int,
        number_of_samples_to_run: int,
        samples_with_errors: Iterable[str] | None,
    ) -> None:
        """Init run stats."""
        self.__number_of_samples = number_of_samples
        self.__number_of_samples_to_run = number_of_samples_to_run

        self.__samples_with_errors = (
            list(samples_with_errors) if samples_with_errors is not None else []
        )

    def number_of_samples(self) -> int:
        """Get number of samples."""
        return self.__number_of_samples

    def number_of_samples_to_run(self) -> int:
        """Get number of samples to run."""
        return self.__number_of_samples_to_run

    def samples_with_errors(self) -> list[str]:
        """Get samples with errors."""
        return self.__samples_with_errors

    def add_samples_to_run(self, addition: int) -> None:
        """Add samples to run."""
        self.__number_of_samples_to_run += addition

    def add_samples_with_errors(self, samples: Iterable[smp_items.Item]) -> None:
        """Add samples with errors."""
        self.__samples_with_errors.extend(sample.exp_sample_id() for sample in samples)


class RunStatsOnlyOptions(RunStatsWithOptions):
    """Experiment run stats for tools with only options."""


class RunStatsWithArguments(RunStatsWithOptions):
    """Experiment run stats for tools with arguments."""

    @classmethod
    def new(cls, data_exp_fs_manager: exp_fs.DataManager) -> Self:
        """Create new run stats."""
        with smp_fs.TSVReader.open(data_exp_fs_manager.samples_tsv()) as smp_tsv_in:
            number_of_samples = sum(1 for _ in smp_tsv_in.iter_row_numbered_items())
        return cls(number_of_samples, 0, None, None)

    def __init__(
        self,
        number_of_samples: int,
        number_of_samples_to_run: int,
        samples_with_missing_inputs: Iterable[str] | None,
        samples_with_errors: Iterable[str] | None,
    ) -> None:
        """Init run stats."""
        super().__init__(
            number_of_samples,
            number_of_samples_to_run,
            samples_with_errors,
        )
        self.__samples_with_missing_inputs = (
            list(samples_with_missing_inputs)
            if samples_with_missing_inputs is not None
            else []
        )

    def samples_with_missing_inputs(self) -> list[str]:
        """Get samples with missing inputs."""
        return self.__samples_with_missing_inputs
