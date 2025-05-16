"""Experiment complete job logics."""

from __future__ import annotations

import logging
import shutil
import time
from itertools import chain

import rich.progress as rich_prog

import pbfbench.experiment.bash.items as exp_bash_items
import pbfbench.experiment.errors as exp_errors
import pbfbench.experiment.file_system as exp_fs
import pbfbench.experiment.slurm.status as exp_slurm_status
import pbfbench.experiment.stats as exp_stats
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.slurm.status as smp_slurm_status
import pbfbench.samples.status as smp_status
import pbfbench.slurm.bash as slurm_bash
import pbfbench.slurm.status as slurm_status
from pbfbench import root_logging

_LOGGER = logging.getLogger(__name__)


def complete_experiment(
    not_finished_samples: list[smp_fs.RowNumberedItem],
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
    run_stats: exp_stats.RunStatsWithOptions,
) -> None:
    """Complete experiment."""
    _finished_job_deamon(
        not_finished_samples,
        data_exp_fs_manager,
        work_exp_fs_manager,
        run_stats,
    )

    _clean_work_directory(work_exp_fs_manager)


def _finished_job_deamon(
    not_finished_samples: list[smp_fs.RowNumberedItem],
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
    run_stats: exp_stats.RunStatsWithOptions,
) -> None:
    """Run finished job deamon."""
    array_job_id = _get_array_job_id(work_exp_fs_manager)

    in_running_job_ids: list[tuple[str, smp_fs.RowNumberedItem]] = [
        (
            slurm_bash.array_task_job_id(
                array_job_id,
                str(smp_fs.to_line_number_base_one(running_sample)),
            ),
            running_sample,
        )
        for running_sample in not_finished_samples
    ]

    with rich_prog.Progress(console=root_logging.CONSOLE) as progress:
        slurm_running_task = progress.add_task(
            "Slurm running",
            total=len(in_running_job_ids),
        )

        while in_running_job_ids:
            time.sleep(60)

            _tmp_in_running_job_ids: list[tuple[str, smp_fs.RowNumberedItem]] = []
            finished_ok_jobs: list[
                tuple[str, smp_fs.RowNumberedItem, slurm_status.SACCTState | None]
            ] = []
            finished_error_jobs: list[
                tuple[str, smp_fs.RowNumberedItem, slurm_status.SACCTState | None]
            ] = []
            for job_id, row_numbered_item in in_running_job_ids:
                sample_status, sacct_state = _get_job_status(
                    work_exp_fs_manager,
                    job_id,
                )
                match sample_status:
                    case smp_status.OKStatus.OK:
                        finished_ok_jobs.append(
                            (job_id, row_numbered_item, sacct_state),
                        )

                    case smp_status.ErrorStatus.ERROR:
                        finished_error_jobs.append(
                            (job_id, row_numbered_item, sacct_state),
                        )

                    case smp_status.ErrorStatus.NOT_RUN:
                        _tmp_in_running_job_ids.append((job_id, row_numbered_item))

            _manage_finished_job(
                finished_ok_jobs,
                finished_error_jobs,
                data_exp_fs_manager,
                work_exp_fs_manager,
                run_stats,
            )

            progress.update(
                slurm_running_task,
                advance=(len(in_running_job_ids) - len(_tmp_in_running_job_ids)),
            )
            in_running_job_ids = _tmp_in_running_job_ids


def _get_array_job_id(work_exp_fs_manager: exp_fs.WorkManager) -> str:
    """Wait the tmp array job id file is created and extract the array job id."""
    while (
        not work_exp_fs_manager.slurm_log_fs_manager()
        .job_id_file_manager()
        .path()
        .exists()
    ):
        time.sleep(10)
    return work_exp_fs_manager.slurm_log_fs_manager().job_id_file_manager().get_job_id()


def _get_job_status(
    work_exp_fs_manager: exp_fs.WorkManager,
    sample_job_id: str,
) -> tuple[smp_status.Status, slurm_status.SACCTState | None]:
    """Get sample experiment status from job id."""
    states = slurm_bash.get_states([sample_job_id])
    if sample_job_id not in states:
        if (
            work_exp_fs_manager.slurm_log_fs_manager()
            .script_step_status_file(
                sample_job_id,
                exp_bash_items.Steps.CLOSE_ENV,
                exp_slurm_status.ScriptSteps.OK,
            )
            .exists()
        ):
            return smp_status.OKStatus.OK, None
        return smp_status.ErrorStatus.ERROR, None
    return smp_status.from_sacct_state(states[sample_job_id]), states[sample_job_id]


def _manage_finished_job(
    ok_job_ids: list[
        tuple[str, smp_fs.RowNumberedItem, slurm_status.SACCTState | None]
    ],
    error_job_ids: list[
        tuple[str, smp_fs.RowNumberedItem, slurm_status.SACCTState | None]
    ],
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
    run_stats: exp_stats.RunStatsWithOptions,
) -> None:
    for job_id, row_numbered_item, _ in ok_job_ids:
        _manage_finished_ok_job(
            job_id,
            row_numbered_item,
            work_exp_fs_manager,
        )
    if error_job_ids:
        with exp_errors.ErrorsTSVWriter.open(
            data_exp_fs_manager.errors_tsv(),
            "a",
        ) as out_exp_errors:
            for job_id, row_numbered_item, _ in error_job_ids:
                _manage_finished_error_job(
                    job_id,
                    row_numbered_item,
                    work_exp_fs_manager,
                    run_stats,
                    out_exp_errors,
                )
        run_stats.add_samples_with_errors(
            (row_numbered_item.item() for _, row_numbered_item, _ in error_job_ids),
        )

    for job_id, row_numbered_item, sacct_state in chain(ok_job_ids, error_job_ids):
        _move_slurm_logs_to_work_sample_dir(
            job_id,
            row_numbered_item,
            sacct_state,
            work_exp_fs_manager,
        )
        _move_work_sample_dir_to_data_dir(
            row_numbered_item,
            work_exp_fs_manager,
            data_exp_fs_manager,
        )


def _manage_finished_ok_job(
    job_id: str,
    row_numbered_item: smp_fs.RowNumberedItem,
    work_exp_fs_manager: exp_fs.WorkManager,
) -> None:
    sample_fs_manager = work_exp_fs_manager.sample_fs_manager(row_numbered_item.item())
    shutil.copy(
        work_exp_fs_manager.slurm_log_fs_manager().stdout(job_id),
        sample_fs_manager.done_log(),
    )


def _manage_finished_error_job(
    job_id: str,
    row_numbered_item: smp_fs.RowNumberedItem,
    work_exp_fs_manager: exp_fs.WorkManager,
    run_stats: exp_stats.RunStatsWithOptions,
    out_exp_errors: exp_errors.ErrorsTSVWriter,
) -> None:
    sample_fs_manager = work_exp_fs_manager.sample_fs_manager(row_numbered_item.item())
    shutil.copy(
        work_exp_fs_manager.slurm_log_fs_manager().stderr(job_id),
        sample_fs_manager.errors_log(),
    )
    run_stats.samples_with_errors().append(row_numbered_item.item().exp_sample_id())
    out_exp_errors.write_error_sample(
        exp_errors.SampleError(
            row_numbered_item.item().exp_sample_id(),
            smp_status.ErrorStatus.ERROR,
        ),
    )


def _move_slurm_logs_to_work_sample_dir(
    job_id: str,
    row_numbered_item: smp_fs.RowNumberedItem,
    sacct_state: slurm_status.SACCTState | None,
    work_exp_fs_manager: exp_fs.WorkManager,
) -> None:
    sample_fs_manager = work_exp_fs_manager.sample_fs_manager(row_numbered_item.item())
    smp_slurm_fs_manager = sample_fs_manager.slurm_fs_manager()

    smp_slurm_fs_manager.slurm_dir().mkdir(parents=True, exist_ok=True)

    if sacct_state is not None:
        smp_slurm_fs_manager.job_state_file_builder().path(sacct_state).touch()

    slurm_bash.write_slurm_stats(job_id, smp_slurm_fs_manager.stats_psv())

    shutil.copy(
        work_exp_fs_manager.slurm_log_fs_manager().stdout(job_id),
        smp_slurm_fs_manager.stdout_log(),
    )
    work_exp_fs_manager.slurm_log_fs_manager().stdout(job_id).unlink()
    shutil.copy(
        work_exp_fs_manager.slurm_log_fs_manager().stderr(job_id),
        smp_slurm_fs_manager.stderr_log(),
    )
    work_exp_fs_manager.slurm_log_fs_manager().stderr(job_id).unlink()

    _command_steps_process_from_slurm_logs(work_exp_fs_manager, job_id).to_yaml(
        smp_slurm_fs_manager.command_steps_status_file_manager().path(),
    )


def _command_steps_process_from_slurm_logs(
    work_exp_fs_manager: exp_fs.WorkManager,
    job_id: str,
) -> smp_slurm_status.CommandStepsProcess:
    def _script_step_status_from_files(
        step: exp_bash_items.Steps,
    ) -> exp_slurm_status.ScriptSteps:
        ok_file = work_exp_fs_manager.slurm_log_fs_manager().script_step_status_file(
            job_id,
            step,
            exp_slurm_status.ScriptSteps.OK,
        )
        error_file = work_exp_fs_manager.slurm_log_fs_manager().script_step_status_file(
            job_id,
            step,
            exp_slurm_status.ScriptSteps.ERROR,
        )
        if ok_file.exists():
            status = exp_slurm_status.ScriptSteps.OK
        elif error_file.exists():
            status = exp_slurm_status.ScriptSteps.ERROR
        else:
            status = exp_slurm_status.ScriptSteps.NULL
        ok_file.unlink(missing_ok=True)
        error_file.unlink(missing_ok=True)
        return status

    return smp_slurm_status.CommandStepsProcess(
        _script_step_status_from_files(
            exp_bash_items.Steps.INIT_ENV,
        ),
        _script_step_status_from_files(
            exp_bash_items.Steps.COMMAND,
        ),
        _script_step_status_from_files(
            exp_bash_items.Steps.CLOSE_ENV,
        ),
    )


def _move_work_sample_dir_to_data_dir(
    row_numbered_item: smp_fs.RowNumberedItem,
    work_exp_fs_manager: exp_fs.WorkManager,
    data_exp_fs_manager: exp_fs.DataManager,
) -> None:
    work_sample_fs_manager = work_exp_fs_manager.sample_fs_manager(
        row_numbered_item.item(),
    )
    data_sample_fs_manager = data_exp_fs_manager.sample_fs_manager(
        row_numbered_item.item(),
    )
    shutil.rmtree(data_sample_fs_manager.sample_dir(), ignore_errors=True)
    shutil.copytree(
        work_sample_fs_manager.sample_dir(),
        data_sample_fs_manager.sample_dir(),
    )
    shutil.rmtree(work_sample_fs_manager.sample_dir(), ignore_errors=True)


def _clean_work_directory(work_exp_fs_manager: exp_fs.WorkManager) -> None:
    """Move work to data."""
    _LOGGER.info("Cleaning work directory")
    #
    # Clean log directory
    #
    work_exp_fs_manager.slurm_log_fs_manager().job_id_file_manager().path().unlink()
    if not any(work_exp_fs_manager.slurm_log_fs_manager().log_dir().iterdir()):
        work_exp_fs_manager.slurm_log_fs_manager().log_dir().rmdir()

    #
    # Clean scripts directory
    #
    work_exp_fs_manager.scripts_fs_manager().sbatch_script().unlink()
    for step in exp_bash_items.Steps:
        work_exp_fs_manager.scripts_fs_manager().step_script(step).unlink()
    if not any(work_exp_fs_manager.scripts_fs_manager().scripts_dir().iterdir()):
        work_exp_fs_manager.scripts_fs_manager().scripts_dir().rmdir()

    #
    # Clean experiment files
    #
    work_exp_fs_manager.config_yaml().unlink()
    work_exp_fs_manager.date_txt().unlink()

    #
    # Try to remove empty tree
    #
    tree_to_remove = [
        work_exp_fs_manager.root_dir(),
        work_exp_fs_manager.topic_dir(),
        work_exp_fs_manager.tool_dir(),
        work_exp_fs_manager.exp_dir(),
    ]
    last_empty = True
    while tree_to_remove and last_empty:
        dir_to_remove = tree_to_remove.pop()
        if not any(dir_to_remove.iterdir()):
            dir_to_remove.rmdir()
        else:
            last_empty = False
