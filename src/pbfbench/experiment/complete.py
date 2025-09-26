"""Experiment complete job logics."""

from __future__ import annotations

import logging
import shutil
import time
from itertools import chain

import rich.progress as rich_prog

import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.slurm.status as smp_slurm_status
import pbfbench.samples.status as smp_status
import pbfbench.slurm.bash as slurm_bash
from pbfbench import root_logging
from pbfbench.slurm import sacct

from . import errors as exp_errors
from . import file_system as exp_fs
from . import managers as exp_managers
from .bash import items as exp_bash_items
from .slurm import checks as exp_slurm_checks
from .slurm import status as exp_slurm_status

_LOGGER = logging.getLogger(__name__)


def complete_experiment(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    unresolved_samples: list[smp_fs.RowNumberedItem],
    array_job_id: str,
) -> None:
    """Complete experiment."""
    _finished_job_deamon(exp_manager, unresolved_samples, array_job_id)

    _clean_work_directory(exp_manager)


def _finished_job_deamon(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    unresolved_samples: list[smp_fs.RowNumberedItem],
    array_job_id: str,
) -> None:
    """Run finished job deamon."""
    in_running_job_ids: list[tuple[str, smp_fs.RowNumberedItem]] = [
        (
            slurm_bash.array_task_job_id(
                array_job_id,
                str(smp_fs.to_line_number_base_one(running_sample)),
            ),
            running_sample,
        )
        for running_sample in unresolved_samples
    ]

    with rich_prog.Progress(console=root_logging.CONSOLE) as progress:
        slurm_running_task = progress.add_task(
            "Slurm running",
            total=len(in_running_job_ids),
        )

        while in_running_job_ids:
            time.sleep(30)

            _tmp_in_running_job_ids: list[tuple[str, smp_fs.RowNumberedItem]] = []
            finished_ok_jobs: list[
                tuple[str, smp_fs.RowNumberedItem, sacct.State | None]
            ] = []
            finished_error_jobs: list[
                tuple[str, smp_fs.RowNumberedItem, sacct.State | None]
            ] = []
            for job_id, row_numbered_item in in_running_job_ids:
                sample_status, sacct_state = _get_job_status(exp_manager, job_id)
                match sample_status:
                    case smp_status.OK.OK:
                        finished_ok_jobs.append(
                            (job_id, row_numbered_item, sacct_state),
                        )

                    case smp_status.Error.ERROR:
                        finished_error_jobs.append(
                            (job_id, row_numbered_item, sacct_state),
                        )

                    case smp_status.Error.NOT_RUN:
                        _tmp_in_running_job_ids.append((job_id, row_numbered_item))

            _manage_finished_job(finished_ok_jobs, finished_error_jobs, exp_manager)

            progress.update(
                slurm_running_task,
                advance=(len(in_running_job_ids) - len(_tmp_in_running_job_ids)),
            )
            in_running_job_ids = _tmp_in_running_job_ids


def _get_job_status(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    sample_job_id: str,
) -> tuple[smp_status.Status, sacct.State | None]:
    """Get sample experiment status from job id."""
    sacct_states = slurm_bash.get_states([sample_job_id])
    #
    # Unknown sacct state
    #
    if sample_job_id not in sacct_states:
        # The job terminated with a success
        if (
            exp_manager.work_fs_manager()
            .slurm_log_fs_manager()
            .script_step_status_file(
                sample_job_id,
                exp_bash_items.Steps.CLOSE_ENV,
                exp_slurm_status.ScriptSteps.OK,
            )
            .exists()
        ):
            return smp_status.OK.OK, None
        # The job did not terminate or with an error
        return smp_status.Error.ERROR, None
    return smp_status.from_sacct_state(sacct_states[sample_job_id]), sacct_states[
        sample_job_id
    ]


def _manage_finished_job(
    ok_job_ids: list[tuple[str, smp_fs.RowNumberedItem, sacct.State | None]],
    error_job_ids: list[tuple[str, smp_fs.RowNumberedItem, sacct.State | None]],
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> None:
    for job_id, row_numbered_item, _ in ok_job_ids:
        _manage_finished_ok_job(
            job_id,
            row_numbered_item,
            exp_manager,
        )
    if error_job_ids:
        _manage_finished_error_jobs(error_job_ids, exp_manager)

    for job_id, row_numbered_item, sacct_state in chain(ok_job_ids, error_job_ids):
        _move_slurm_logs_to_work_sample_dir(
            job_id,
            row_numbered_item,
            sacct_state,
            exp_manager,
        )
        _move_work_sample_dir_to_data_dir(row_numbered_item, exp_manager)


def _manage_finished_ok_job(
    job_id: str,
    row_numbered_item: smp_fs.RowNumberedItem,
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> None:
    sample_fs_manager = exp_manager.work_fs_manager().sample_fs_manager(
        row_numbered_item.item(),
    )
    shutil.copy(
        exp_manager.work_fs_manager().slurm_log_fs_manager().stdout(job_id),
        sample_fs_manager.done_log(),
    )


def _manage_finished_error_jobs(
    error_job_ids: list[tuple[str, smp_fs.RowNumberedItem, sacct.State | None]],
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> None:
    for job_id, row_numbered_item, _ in error_job_ids:
        sample_fs_manager = exp_manager.work_fs_manager().sample_fs_manager(
            row_numbered_item.item(),
        )
        shutil.copy(
            exp_manager.work_fs_manager().slurm_log_fs_manager().stderr(job_id),
            sample_fs_manager.errors_log(),
        )

    exp_errors.write_errors(
        exp_manager.data_fs_manager(),
        (sample for _, sample, _ in error_job_ids),
    )


def _move_slurm_logs_to_work_sample_dir(
    job_id: str,
    row_numbered_item: smp_fs.RowNumberedItem,
    sacct_state: sacct.State | None,
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> None:
    sample_fs_manager = exp_manager.work_fs_manager().sample_fs_manager(
        row_numbered_item.item(),
    )
    smp_slurm_fs_manager = sample_fs_manager.slurm_fs_manager()

    smp_slurm_fs_manager.slurm_dir().mkdir(parents=True, exist_ok=True)

    if sacct_state is not None:
        smp_slurm_fs_manager.job_state_file_builder().path(sacct_state).touch()

    slurm_bash.write_slurm_stats(job_id, smp_slurm_fs_manager.stats_psv())

    shutil.copy(
        exp_manager.work_fs_manager().slurm_log_fs_manager().stdout(job_id),
        smp_slurm_fs_manager.stdout_log(),
    )
    exp_manager.work_fs_manager().slurm_log_fs_manager().stdout(job_id).unlink()
    shutil.copy(
        exp_manager.work_fs_manager().slurm_log_fs_manager().stderr(job_id),
        smp_slurm_fs_manager.stderr_log(),
    )
    exp_manager.work_fs_manager().slurm_log_fs_manager().stderr(job_id).unlink()

    _command_steps_process_from_slurm_logs(
        exp_manager.work_fs_manager(),
        job_id,
    ).to_yaml(
        smp_slurm_fs_manager.command_steps_status_file_manager().path(),
    )


def _command_steps_process_from_slurm_logs(
    work_exp_fs_manager: exp_fs.WorkManager,
    job_id: str,
) -> smp_slurm_status.CommandStepsProcess:
    return smp_slurm_status.CommandStepsProcess(
        exp_slurm_checks.script_step_status(
            work_exp_fs_manager,
            job_id,
            exp_bash_items.Steps.INIT_ENV,
        ),
        exp_slurm_checks.script_step_status(
            work_exp_fs_manager,
            job_id,
            exp_bash_items.Steps.COMMAND,
        ),
        exp_slurm_checks.script_step_status(
            work_exp_fs_manager,
            job_id,
            exp_bash_items.Steps.CLOSE_ENV,
        ),
    )


def _move_work_sample_dir_to_data_dir(
    row_numbered_item: smp_fs.RowNumberedItem,
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> None:
    work_sample_fs_manager = exp_manager.work_fs_manager().sample_fs_manager(
        row_numbered_item.item(),
    )
    data_sample_fs_manager = exp_manager.data_fs_manager().sample_fs_manager(
        row_numbered_item.item(),
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
    #
    # Clean log directory
    #
    exp_manager.work_fs_manager().slurm_log_fs_manager().job_id_file_manager().path().unlink()
    if not any(
        exp_manager.work_fs_manager().slurm_log_fs_manager().log_dir().iterdir(),
    ):
        exp_manager.work_fs_manager().slurm_log_fs_manager().log_dir().rmdir()

    #
    # Clean scripts directory
    #
    exp_manager.work_fs_manager().scripts_fs_manager().sbatch_script().unlink()
    for step in exp_bash_items.Steps:
        exp_manager.work_fs_manager().scripts_fs_manager().step_script(step).unlink()
    if not any(
        exp_manager.work_fs_manager().scripts_fs_manager().scripts_dir().iterdir(),
    ):
        exp_manager.work_fs_manager().scripts_fs_manager().scripts_dir().rmdir()

    #
    # Clean experiment files
    #
    exp_manager.work_fs_manager().config_yaml().unlink()

    #
    # Try to remove empty tree
    #
    tree_to_remove = [
        exp_manager.work_fs_manager().root_dir(),
        exp_manager.work_fs_manager().topic_dir(),
        exp_manager.work_fs_manager().tool_dir(),
        exp_manager.work_fs_manager().exp_dir(),
    ]
    last_empty = True
    while tree_to_remove and last_empty:
        dir_to_remove = tree_to_remove.pop()
        if not any(dir_to_remove.iterdir()):
            dir_to_remove.rmdir()
        else:
            last_empty = False
