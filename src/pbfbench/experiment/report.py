"""Experiment report module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

import pbfbench.samples.status as smp_status
import pbfbench.slurm.bash as slurm_bash
from pbfbench.slurm import sacct
from pbfbench.yaml_interface import YAMLInterface

from . import file_system as exp_fs
from . import in_progress, stats
from . import iter as exp_iter

if TYPE_CHECKING:
    from yaml import YAMLObject  # type: ignore[import-untyped]


@final
class RunningExperiment(YAMLInterface):
    """Running experiment metadata."""

    KEY_IN_PROGRESS_DATA = "in_progress_data"
    KEY_SACCT_STATE = "sacct_state"

    @classmethod
    def from_yaml_load(cls, pyyaml_obj: dict[str, YAMLObject]) -> Self:
        """Convert dict to object."""
        sacct_state = (
            sacct.State(pyyaml_obj[cls.KEY_SACCT_STATE])
            if pyyaml_obj[cls.KEY_SACCT_STATE] is not None
            else None
        )
        return cls(
            in_progress.InDataDirectory.from_yaml_load(
                pyyaml_obj[cls.KEY_IN_PROGRESS_DATA],
            ),
            sacct_state,
        )

    def __init__(
        self,
        in_progress_data: in_progress.InDataDirectory,
        sacct_state: sacct.State | None,
    ) -> None:
        self._in_progress_data = in_progress_data
        self._sacct_state = sacct_state

    def in_progress_data(self) -> in_progress.InDataDirectory:
        """Get in progress metadata in the data directory."""
        return self._in_progress_data

    def sacct_state(self) -> sacct.State | None:
        """Get sacct state."""
        return self._sacct_state

    def to_yaml_dump(self) -> dict[str, YAMLObject]:
        """Convert to dict."""
        return {
            self.KEY_IN_PROGRESS_DATA: self._in_progress_data.to_yaml_dump(),
            self.KEY_SACCT_STATE: (
                self._sacct_state.value if self._sacct_state is not None else None
            ),
        }


def running_experiment_to_str(running_experiment: RunningExperiment) -> str:
    """Convert running experiment to string."""
    return (
        f"Experiment is running\n"
        f"* Experiment launched the: {running_experiment.in_progress_data().date()}\n"
        f"* Working directory root path:"
        f" {running_experiment.in_progress_data().working_directory()}\n"
        f"* SLURM job ID: {running_experiment.in_progress_data().job_id()}\n"
        f"* SACCT state: {running_experiment.sacct_state()}\n"
    )


def running_experiment(
    data_exp_fs_manager: exp_fs.DataManager,
) -> RunningExperiment | None:
    """Check if experiment is running."""
    if not data_exp_fs_manager.in_progress_yaml().exists():
        return None

    in_progress_data = in_progress.InDataDirectory.from_yaml(
        data_exp_fs_manager.in_progress_yaml(),
    )
    return RunningExperiment(
        in_progress_data,
        slurm_bash.get_state(in_progress_data.job_id()),
    )


def samples_stats(data_exp_manager: exp_fs.DataManager) -> stats.Samples:
    """Get samples stats."""
    status_number = smp_status.StatusMap[int].default(0)
    for _, status in exp_iter.samples_with_status(data_exp_manager):
        status_number[status] += 1
    return stats.Samples.from_status_map(status_number)


@final
class Report(YAMLInterface):
    """report metadata."""

    KEY_RUNNING_EXPERIMENT = "running_experiment"
    KEY_SAMPLES_STATS = "samples_stats"

    @classmethod
    def from_data_exp_fs_manager(cls, data_exp_manager: exp_fs.DataManager) -> Self:
        """Generate report."""
        return cls(
            running_experiment(data_exp_manager),
            samples_stats(data_exp_manager),
        )

    @classmethod
    def from_yaml_load(cls, pyyaml_obj: dict[str, YAMLObject]) -> Self:
        """Convert dict to object."""
        running_experiment = (
            RunningExperiment.from_yaml_load(pyyaml_obj[cls.KEY_RUNNING_EXPERIMENT])
            if pyyaml_obj[cls.KEY_RUNNING_EXPERIMENT] is not None
            else None
        )
        return cls(
            running_experiment,
            stats.Samples.from_yaml_load(pyyaml_obj[cls.KEY_SAMPLES_STATS]),
        )

    def __init__(
        self,
        running_experiment: RunningExperiment | None,
        samples_stats: stats.Samples,
    ) -> None:
        self._running_experiment = running_experiment
        self._samples_stats = samples_stats

    def running_experiment(self) -> RunningExperiment | None:
        """Get running experiment."""
        return self._running_experiment

    def samples_stats(self) -> stats.Samples:
        """Get samples stats."""
        return self._samples_stats

    def to_yaml_dump(self) -> dict[str, YAMLObject]:
        """Convert to dict."""
        return {
            self.KEY_RUNNING_EXPERIMENT: (
                self._running_experiment.to_yaml_dump()
                if self._running_experiment is not None
                else None
            ),
            self.KEY_SAMPLES_STATS: self._samples_stats.to_yaml_dump(),
        }


def report_to_string(report: Report) -> str:
    """Convert report to string.

    Notes
    -----
    There is no leading new line.
    """
    running_exp = report.running_experiment()
    return (
        (
            "Experiment is not running\n"
            if running_exp is None
            else f"{running_experiment_to_str(running_exp)}\n"
        )
        + "Samples stats:\n"
        "* Total number of samples:"
        f" {report.samples_stats().total_number_of_samples()}\n"
        "* Number of successful samples:"
        f" {report.samples_stats().number_of_successful_samples()}\n"
        "* Number of samples with missing inputs:"
        f" {report.samples_stats().number_of_samples_with_missing_inputs()}\n"
        "* Number of failed samples:"
        f" {report.samples_stats().number_of_failed_samples()}\n"
        "* Number of not run samples:"
        f" {report.samples_stats().number_of_not_run_samples()}"
    )
