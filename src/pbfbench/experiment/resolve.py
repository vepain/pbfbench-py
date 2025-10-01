"""Experiment complete job logics."""

from __future__ import annotations

import logging
import shutil
import time
from itertools import chain
from typing import TYPE_CHECKING, Self

import rich.progress as rich_prog

import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.slurm.status as smp_slurm_status
import pbfbench.samples.status as smp_status
import pbfbench.slurm.bash as slurm_bash
from pbfbench import root_logging

from . import errors as exp_errors
from . import history, monitors
from . import managers as exp_managers
from .bash import items as exp_bash_items
from .slurm import checks as exp_slurm_checks
from .slurm import status as exp_slurm_status

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from pbfbench.slurm import sacct

_LOGGER = logging.getLogger(__name__)


def resolve_running_samples(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    unresolved_samples: list[smp_fs.RowNumberedItem],
    array_job_id: str,
) -> None:
    """Complete experiment."""
    _finished_job_deamon(exp_manager, unresolved_samples, array_job_id)
    history.update_history(exp_manager)
    _clean_work_directory(exp_manager)


def _finished_job_deamon(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    unresolved_samples: list[smp_fs.RowNumberedItem],
    array_job_id: str,
) -> None:
    """Run finished job deamon."""
    in_running_job_ids = _running_job_ids(array_job_id, unresolved_samples)

    with rich_prog.Progress(console=root_logging.CONSOLE) as progress:
        slurm_running_task = progress.add_task(
            "Slurm running",
            total=len(in_running_job_ids),
        )

        while in_running_job_ids:
            time.sleep(10)

            _tmp_in_running_job_ids, resolved_samples = _get_resolved_samples(
                exp_manager,
                in_running_job_ids,
            )

            _manage_finished_job(resolved_samples, exp_manager)

            progress.update(
                slurm_running_task,
                advance=(len(in_running_job_ids) - len(_tmp_in_running_job_ids)),
            )
            in_running_job_ids = _tmp_in_running_job_ids


def _get_resolved_samples(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    in_running_job_ids: list[RunningJobID],
) -> tuple[list[RunningJobID], ResolvedSamples]:
    """Get resolved samples."""
    _tmp_in_running_job_ids: list[RunningJobID] = []
    resolved_samples = ResolvedSamples.new()

    for running_job_id in in_running_job_ids:
        sample_status, sacct_state = _get_job_status(
            exp_manager,
            running_job_id,
        )
        match sample_status:
            case smp_status.OK.OK:
                resolved_samples.ok_samples().append(
                    ResolvedJobID.from_running_job_id(
                        running_job_id,
                        sample_status,
                        sacct_state,
                    ),
                )
            case smp_status.Error.ERROR:
                resolved_samples.error_samples().append(
                    ResolvedJobID.from_running_job_id(
                        running_job_id,
                        sample_status,
                        sacct_state,
                    ),
                )
            case smp_status.Error.NOT_RUN:
                _tmp_in_running_job_ids.append(running_job_id)

    return _tmp_in_running_job_ids, resolved_samples


class RunningJobID:
    """Running job ID."""

    @classmethod
    def from_array_job_id(
        cls,
        array_job_id: str,
        row_numbered_item: smp_fs.RowNumberedItem,
    ) -> Self:
        """Get running job ID from array job ID and row numbered item."""
        return cls(
            slurm_bash.array_task_job_id(
                array_job_id,
                str(smp_fs.to_line_number_base_one(row_numbered_item)),
            ),
            row_numbered_item,
        )

    def __init__(self, job_id: str, row_numbered_item: smp_fs.RowNumberedItem) -> None:
        self.__job_id = job_id
        self.__row_numbered_item = row_numbered_item

    def job_id(self) -> str:
        """Get job id."""
        return self.__job_id

    def row_numbered_item(self) -> smp_fs.RowNumberedItem:
        """Get row numbered item."""
        return self.__row_numbered_item


def _running_job_ids(
    array_job_id: str,
    unresolved_samples: list[smp_fs.RowNumberedItem],
) -> list[RunningJobID]:
    """Get the list of running job IDs."""
    return [
        RunningJobID.from_array_job_id(array_job_id, running_sample)
        for running_sample in unresolved_samples
    ]


class ResolvedJobID:
    """Resolved job ID."""

    @classmethod
    def from_running_job_id(
        cls,
        running_job_id: RunningJobID,
        status: smp_status.Status,
        sacct_state: sacct.State | None,
    ) -> Self:
        """Get resolved job ID from running job ID and sacct state."""
        return cls(
            running_job_id.job_id(),
            running_job_id.row_numbered_item(),
            status,
            sacct_state,
        )

    def __init__(
        self,
        job_id: str,
        row_numbered_item: smp_fs.RowNumberedItem,
        status: smp_status.Status,
        sacct_state: sacct.State | None,
    ) -> None:
        self.__job_id = job_id
        self.__row_numbered_item = row_numbered_item
        self.__status = status
        self.__sacct_state = sacct_state

    def job_id(self) -> str:
        """Get job id."""
        return self.__job_id

    def row_numbered_item(self) -> smp_fs.RowNumberedItem:
        """Get row numbered item."""
        return self.__row_numbered_item

    def status(self) -> smp_status.Status:
        """Get status."""
        return self.__status

    def sacct_state(self) -> sacct.State | None:
        """Get sacct state."""
        return self.__sacct_state


def _get_job_status(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    running_job_id: RunningJobID,
) -> tuple[smp_status.Status, sacct.State | None]:
    """Get sample experiment status from job id."""
    sacct_states = slurm_bash.get_states([running_job_id.job_id()])
    #
    # Unknown sacct state
    #
    if running_job_id.job_id() not in sacct_states:
        # The job terminated with a success
        if (
            exp_manager.work_fs_manager()
            .slurm_log_fs_manager()
            .script_step_status_file(
                running_job_id.job_id(),
                exp_bash_items.Steps.CLOSE_ENV,
                exp_slurm_status.ScriptSteps.OK,
            )
            .exists()
        ):
            return smp_status.OK.OK, None
        # The job did not terminate or with an error
        return smp_status.Error.ERROR, None
    return smp_status.from_sacct_state(
        sacct_states[running_job_id.job_id()],
    ), sacct_states[running_job_id.job_id()]


class ResolvedSamples:
    """Resolved samples."""

    @classmethod
    def new(cls) -> Self:
        """Get new resolved samples."""
        return cls([], [])

    def __init__(
        self,
        ok_samples: Iterable[ResolvedJobID],
        error_samples: Iterable[ResolvedJobID],
    ) -> None:
        self.__ok_samples = list(ok_samples)
        self.__error_samples = list(error_samples)

    def ok_samples(self) -> list[ResolvedJobID]:
        """Get ok samples."""
        return self.__ok_samples

    def error_samples(self) -> list[ResolvedJobID]:
        """Get error samples."""
        return self.__error_samples

    def __iter__(self) -> Iterator[ResolvedJobID]:
        """Get iterator."""
        return chain(self.__ok_samples, self.__error_samples)


def _manage_finished_job(
    resolved_samples: ResolvedSamples,
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> None:
    _manage_finished_ok_jobs(resolved_samples, exp_manager)
    _manage_finished_error_jobs(resolved_samples, exp_manager)

    for resolved_job_id in resolved_samples:
        _move_slurm_logs_to_work_sample_dir(resolved_job_id, exp_manager)
        _move_work_sample_dir_to_data_dir(resolved_job_id, exp_manager)

    monitors.update_samples_resolution_status(
        exp_manager.work_fs_manager(),
        (
            (resolved_job_id.row_numbered_item(), resolved_job_id.status())
            for resolved_job_id in resolved_samples
        ),
    )


def _manage_finished_ok_jobs(
    resolved_samples: ResolvedSamples,
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> None:
    for resolved_job_id in resolved_samples.ok_samples():
        slurm_stdout = (
            exp_manager.work_fs_manager()
            .slurm_log_fs_manager()
            .stdout(resolved_job_id.job_id())
        )
        sample_fs_manager = exp_manager.work_fs_manager().sample_fs_manager(
            resolved_job_id.row_numbered_item().item(),
        )
        sample_fs_manager.sample_dir().mkdir(parents=True, exist_ok=True)
        shutil.copy(slurm_stdout, sample_fs_manager.done_log())


def _manage_finished_error_jobs(
    resolved_samples: ResolvedSamples,
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> None:
    for error_job_id in resolved_samples.error_samples():
        slurm_stderr = (
            exp_manager.work_fs_manager()
            .slurm_log_fs_manager()
            .stderr(error_job_id.job_id())
        )
        sample_fs_manager = exp_manager.work_fs_manager().sample_fs_manager(
            error_job_id.row_numbered_item().item(),
        )
        sample_fs_manager.sample_dir().mkdir(parents=True, exist_ok=True)
        shutil.copy(slurm_stderr, sample_fs_manager.errors_log())

    if resolved_samples.error_samples():
        exp_errors.write_errors(
            exp_manager.data_fs_manager(),
            (
                error_job_id.row_numbered_item()
                for error_job_id in resolved_samples.error_samples()
            ),
        )


def _move_slurm_logs_to_work_sample_dir(
    resolved_job_id: ResolvedJobID,
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> None:
    sample_fs_manager = exp_manager.work_fs_manager().sample_fs_manager(
        resolved_job_id.row_numbered_item().item(),
    )
    smp_slurm_fs_manager = sample_fs_manager.slurm_fs_manager()

    smp_slurm_fs_manager.slurm_dir().mkdir(parents=True, exist_ok=True)

    sacct_state = resolved_job_id.sacct_state()
    if sacct_state is not None:
        smp_slurm_fs_manager.job_state_file_builder().path(sacct_state).touch()

    slurm_bash.write_slurm_stats(
        resolved_job_id.job_id(),
        smp_slurm_fs_manager.stats_psv(),
    )

    slurm_stdout = (
        exp_manager.work_fs_manager()
        .slurm_log_fs_manager()
        .stdout(resolved_job_id.job_id())
    )
    shutil.copy(slurm_stdout, smp_slurm_fs_manager.stdout_log())

    slurm_stderr = (
        exp_manager.work_fs_manager()
        .slurm_log_fs_manager()
        .stderr(resolved_job_id.job_id())
    )
    shutil.copy(slurm_stderr, smp_slurm_fs_manager.stderr_log())

    _command_steps_process_from_slurm_logs(exp_manager, resolved_job_id).to_yaml(
        smp_slurm_fs_manager.command_steps_status_file_manager().path(),
    )


def _command_steps_process_from_slurm_logs(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    resolved_job_id: ResolvedJobID,
) -> smp_slurm_status.CommandStepsProcess:
    return smp_slurm_status.CommandStepsProcess(
        exp_slurm_checks.script_step_status(
            exp_manager.work_fs_manager(),
            resolved_job_id.job_id(),
            exp_bash_items.Steps.INIT_ENV,
        ),
        exp_slurm_checks.script_step_status(
            exp_manager.work_fs_manager(),
            resolved_job_id.job_id(),
            exp_bash_items.Steps.COMMAND,
        ),
        exp_slurm_checks.script_step_status(
            exp_manager.work_fs_manager(),
            resolved_job_id.job_id(),
            exp_bash_items.Steps.CLOSE_ENV,
        ),
    )


def _move_work_sample_dir_to_data_dir(
    resolved_job_id: ResolvedJobID,
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> None:
    work_sample_fs_manager = exp_manager.work_fs_manager().sample_fs_manager(
        resolved_job_id.row_numbered_item().item(),
    )
    data_sample_fs_manager = exp_manager.data_fs_manager().sample_fs_manager(
        resolved_job_id.row_numbered_item().item(),
    )
    shutil.rmtree(data_sample_fs_manager.sample_dir(), ignore_errors=True)
    shutil.copytree(
        work_sample_fs_manager.sample_dir(),
        data_sample_fs_manager.sample_dir(),
    )
    shutil.rmtree(work_sample_fs_manager.sample_dir(), ignore_errors=True)


def _clean_work_directory(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> None:
    """Move work to data."""
    _LOGGER.info("Cleaning work directory")
    shutil.rmtree(exp_manager.work_fs_manager().exp_dir(), ignore_errors=True)
    #
    # Try to remove empty parent directories
    #
    tree_to_remove = [
        exp_manager.work_fs_manager().root_dir(),
        exp_manager.work_fs_manager().topic_dir(),
        exp_manager.work_fs_manager().tool_dir(),
    ]
    last_empty = True
    while tree_to_remove and last_empty:
        dir_to_remove = tree_to_remove.pop()
        if not any(dir_to_remove.iterdir()):
            dir_to_remove.rmdir()
        else:
            last_empty = False
