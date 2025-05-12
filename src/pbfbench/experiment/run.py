"""Experiment run module."""

from __future__ import annotations

import logging
import shutil
import subprocess
import time
from typing import TYPE_CHECKING

import rich.progress as rich_prog

import pbfbench.abc.tool.config as abc_tool_cfg
import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.abc.topic.results.items as abc_topic_res_items
import pbfbench.experiment.config as exp_cfg
import pbfbench.experiment.errors as exp_errors
import pbfbench.experiment.file_system as exp_fs
import pbfbench.experiment.iter as exp_iter
import pbfbench.experiment.shell as exp_shell
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.status as smp_status
import pbfbench.slurm.shell as slurm_sh
import pbfbench.slurm.status as slurm_status
from pbfbench import root_logging, subprocess_lib

if TYPE_CHECKING:
    from collections.abc import Iterable


_LOGGER = logging.getLogger(__name__)


class RunStats:
    """Experiment run stats."""

    @classmethod
    def new(cls, data_exp_fs_manager: exp_fs.DataManager) -> RunStats:
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
        self.__number_of_samples = number_of_samples
        self.__number_of_samples_to_run = number_of_samples_to_run
        self.__samples_with_missing_inputs = (
            list(samples_with_missing_inputs)
            if samples_with_missing_inputs is not None
            else []
        )
        self.__samples_with_errors = (
            list(samples_with_errors) if samples_with_errors is not None else []
        )

    def number_of_samples(self) -> int:
        """Get number of samples."""
        return self.__number_of_samples

    def number_of_samples_to_run(self) -> int:
        """Get number of samples to run."""
        return self.__number_of_samples_to_run

    def samples_with_missing_inputs(self) -> list[str]:
        """Get samples with missing inputs."""
        return self.__samples_with_missing_inputs

    def samples_with_errors(self) -> list[str]:
        """Get samples with errors."""
        return self.__samples_with_errors

    def add_samples_to_run(self, addition: int) -> None:
        """Add samples to run."""
        self.__number_of_samples_to_run += addition


def run_experiment_on_samples(
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
    exp_config: exp_cfg.Config,
    tool_connector: abc_tool_visitor.Connector,
) -> RunStats:
    """Run the experiment."""
    # REFACTOR use markdon print and do better app prints

    _LOGGER.info(
        "Running experiment `%s` with tool `%s` for the topic `%s`.",
        exp_config.name(),
        tool_connector.description().name(),
        tool_connector.description().topic().name(),
    )

    _init_experiment_file_systems(
        data_exp_fs_manager,
        work_exp_fs_manager,
        exp_config,
    )

    run_stats = RunStats.new(data_exp_fs_manager)

    samples_to_run = _get_samples_to_run(data_exp_fs_manager, run_stats)

    _init_sample_directories(samples_to_run, work_exp_fs_manager)

    (
        checked_inputs_samples_to_run,
        samples_with_missing_inputs,
        names_to_input_results,
    ) = _filter_missing_inputs(
        tool_connector,
        exp_config,
        samples_to_run,
        data_exp_fs_manager,
        work_exp_fs_manager,
    )

    _write_experiment_missing_inputs(
        samples_with_missing_inputs,
        work_exp_fs_manager,
        run_stats,
    )

    if not checked_inputs_samples_to_run:
        _LOGGER.info("No samples to run")
    else:
        _LOGGER.info(
            "Number of samples sent to sbatch: %d",
            len(checked_inputs_samples_to_run),
        )
        _create_and_run_sbatch_script(
            tool_connector,
            names_to_input_results,
            exp_config,
            checked_inputs_samples_to_run,
            data_exp_fs_manager,
            work_exp_fs_manager,
        )

        run_samples_with_status = _wait_all_job_finish(
            checked_inputs_samples_to_run,
            work_exp_fs_manager,
        )

        _manage_all_run_status(
            run_samples_with_status,
            work_exp_fs_manager,
            run_stats,
        )

        _write_sbatch_stats_and_move_slurm_logs(
            run_samples_with_status,
            work_exp_fs_manager,
        )

    _move_work_to_data(
        work_exp_fs_manager,
        data_exp_fs_manager,
        samples_to_run,
    )

    if run_stats.samples_with_missing_inputs() or run_stats.samples_with_errors():
        _LOGGER.info(
            "The list of samples with missing inputs"
            " or which exit with errors is written to file: %s",
            data_exp_fs_manager.errors_tsv(),
        )

    return run_stats


def _init_experiment_file_systems[C: exp_cfg.Config](
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
    exp_config: C,
) -> None:
    """Prepare experiment file systems."""
    data_exp_fs_manager.exp_dir().mkdir(parents=True, exist_ok=True)

    shutil.rmtree(work_exp_fs_manager.exp_dir(), ignore_errors=True)

    work_exp_fs_manager.exp_dir().mkdir(parents=True, exist_ok=True)
    exp_fs.write_formatted_exp_date(work_exp_fs_manager)
    exp_config.to_yaml(work_exp_fs_manager.config_yaml())
    work_exp_fs_manager.scripts_dir().mkdir(parents=True, exist_ok=True)


def _get_samples_to_run(
    data_exp_fs_manager: exp_fs.DataManager,
    run_stats: RunStats,
) -> list[smp_fs.RowNumberedItem]:
    """Get samples to run."""
    with smp_fs.TSVReader.open(data_exp_fs_manager.samples_tsv()) as smp_tsv_in:
        samples_to_run = list(
            exp_iter.samples_with_error_status(
                data_exp_fs_manager,
                smp_tsv_in.iter_row_numbered_items(),
            ),
        )
    run_stats.add_samples_to_run(len(samples_to_run))

    _LOGGER.info("Number of samples to run: %d", len(samples_to_run))

    return samples_to_run


def _init_sample_directories(
    samples_to_run: Iterable[smp_fs.RowNumberedItem],
    work_exp_fs_manager: exp_fs.WorkManager,
) -> None:
    """Prepare sample directories."""
    for run_sample in samples_to_run:
        sample_fs_manager = work_exp_fs_manager.sample_fs_manager(run_sample.item())
        sample_fs_manager.sample_dir().mkdir(parents=True, exist_ok=True)


def _filter_missing_inputs(
    tool_connector: abc_tool_visitor.Connector,
    exp_config: exp_cfg.Config,
    samples_to_run: list[smp_fs.RowNumberedItem],
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
) -> tuple[
    list[smp_fs.RowNumberedItem],
    list[smp_fs.RowNumberedItem],
    dict[abc_tool_cfg.Names, abc_topic_res_items.Result],
]:
    """Filter missing inputs."""
    names_to_input_results = tool_connector.config_to_inputs(
        exp_config,
        data_exp_fs_manager,
    )

    checked_inputs_samples_to_run, samples_with_missing_inputs = (
        exp_iter.checked_input_samples_to_run(
            work_exp_fs_manager,
            samples_to_run,
            names_to_input_results,
        )
    )

    return (
        checked_inputs_samples_to_run,
        samples_with_missing_inputs,
        names_to_input_results,
    )


def _write_experiment_missing_inputs(
    samples_with_missing_inputs: list[smp_fs.RowNumberedItem],
    work_exp_fs_manager: exp_fs.WorkManager,
    run_stats: RunStats,
) -> None:
    """Write experiment missing inputs."""
    run_stats.samples_with_missing_inputs().extend(
        sample.item().exp_sample_id() for sample in samples_with_missing_inputs
    )

    _LOGGER.error("Samples with missing inputs: %d", len(samples_with_missing_inputs))

    with exp_errors.ErrorsTSVWriter.open(
        work_exp_fs_manager.errors_tsv(),
        "w",
    ) as out_exp_errors:
        out_exp_errors.write_error_samples(
            (
                exp_errors.SampleError(
                    sample_id,
                    smp_status.ErrorStatus.MISSING_INPUTS,
                )
                for sample_id in run_stats.samples_with_missing_inputs()
            ),
        )


def _create_and_run_sbatch_script(  # noqa: PLR0913
    tool_connector: abc_tool_visitor.Connector,
    names_to_input_results: dict[abc_tool_cfg.Names, abc_topic_res_items.Result],
    exp_config: exp_cfg.Config,
    checked_inputs_samples_to_run: list[smp_fs.RowNumberedItem],
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
) -> None:
    """Run sbatch script."""
    work_exp_fs_manager.tmp_slurm_logs_dir().mkdir(parents=True, exist_ok=True)
    tool_commands = tool_connector.inputs_to_commands(
        exp_config,
        names_to_input_results,
        work_exp_fs_manager,
    )
    exp_shell.create_run_script(
        data_exp_fs_manager,
        work_exp_fs_manager,
        checked_inputs_samples_to_run,
        exp_config.slurm_config(),
        tool_commands,
    )

    cmd_path = subprocess_lib.command_path(slurm_sh.SBATCH_CMD)
    result = subprocess.run(  # noqa: S603
        [str(x) for x in [cmd_path, work_exp_fs_manager.sbatch_sh_script()]],
        capture_output=True,
        check=False,
    )
    _LOGGER.debug("%s stdout: %s", slurm_sh.SBATCH_CMD, result.stdout)
    _LOGGER.debug("%s stderr: %s", slurm_sh.SBATCH_CMD, result.stderr)


def _wait_all_job_finish(
    checked_inputs_samples_to_run: list[smp_fs.RowNumberedItem],
    work_exp_fs_manager: exp_fs.WorkManager,
) -> list[tuple[smp_fs.RowNumberedItem, slurm_status.Status, str]]:
    """Wait all job finish."""
    array_job_id = _get_array_job_id(work_exp_fs_manager)

    in_running_job_ids: dict[str, smp_fs.RowNumberedItem] = {
        slurm_sh.array_task_job_id(
            array_job_id,
            str(smp_fs.to_line_number_base_one(running_sample)),
        ): running_sample
        for running_sample in checked_inputs_samples_to_run
    }

    run_samples_with_status: list[
        tuple[smp_fs.RowNumberedItem, slurm_status.Status, str]
    ] = []

    with rich_prog.Progress(console=root_logging.CONSOLE) as progress:
        slurm_running_task = progress.add_task(
            "Slurm running",
            total=len(in_running_job_ids),
        )

        while in_running_job_ids:
            time.sleep(60)

            _tmp_in_running_job_ids = {}
            for job_id, row_numbered_item in in_running_job_ids.items():
                status = slurm_status.get_status(work_exp_fs_manager, job_id)
                if status is None:
                    _tmp_in_running_job_ids[job_id] = row_numbered_item
                else:
                    run_samples_with_status.append((row_numbered_item, status, job_id))

            progress.update(
                slurm_running_task,
                advance=(len(in_running_job_ids) - len(_tmp_in_running_job_ids)),
            )
            in_running_job_ids = _tmp_in_running_job_ids

    return run_samples_with_status


def _get_array_job_id(work_exp_fs_manager: exp_fs.WorkManager) -> str:
    """Wait the array job id file is created and extract the array job id."""
    while not work_exp_fs_manager.array_job_id_file().exists():
        time.sleep(10)
    array_job_id = exp_fs.get_array_job_id_from_file(work_exp_fs_manager)
    work_exp_fs_manager.array_job_id_file().unlink()
    return array_job_id


def _manage_all_run_status(
    run_samples_with_status: list[
        tuple[smp_fs.RowNumberedItem, slurm_status.Status, str]
    ],
    work_exp_fs_manager: exp_fs.WorkManager,
    run_stats: RunStats,
) -> None:
    """Write experiment errors."""
    for run_sample, status, job_id in run_samples_with_status:
        sample_fs_manager = work_exp_fs_manager.sample_fs_manager(
            run_sample.item(),
        )
        if _slurm_status_equals_an_exp_sample_error(status):
            run_stats.samples_with_errors().append(run_sample.item().exp_sample_id())
            shutil.copy(
                work_exp_fs_manager.sbatch_err_file(job_id),
                sample_fs_manager.errors_log(),
            )
        else:
            shutil.copy(
                work_exp_fs_manager.sbatch_out_file(job_id),
                sample_fs_manager.done_log(),
            )

    _LOGGER.error("Samples with errors: %d", len(run_stats.samples_with_errors()))

    with exp_errors.ErrorsTSVWriter.open(
        work_exp_fs_manager.errors_tsv(),
        "a",
    ) as out_exp_errors:
        out_exp_errors.write_error_samples(
            (
                exp_errors.SampleError(
                    sample_id,
                    smp_status.ErrorStatus.ERROR,
                )
                for sample_id in run_stats.samples_with_errors()
            ),
        )


def _slurm_status_equals_an_exp_sample_error(status: slurm_status.Status) -> bool:
    match status:
        case slurm_status.Status.INIT_ENV_ERROR | slurm_status.Status.COMMAND_ERROR:
            return True
        case slurm_status.Status.CLOSE_ENV_ERROR | slurm_status.Status.END:
            return False


def _write_sbatch_stats_and_move_slurm_logs(
    run_samples_with_status: list[
        tuple[smp_fs.RowNumberedItem, slurm_status.Status, str]
    ],
    work_exp_fs_manager: exp_fs.WorkManager,
) -> None:
    """Write sbatch stats."""
    for run_sample, _, job_id in run_samples_with_status:
        sample_fs_manager = work_exp_fs_manager.sample_fs_manager(run_sample.item())
        slurm_sh.write_slurm_stats(job_id, sample_fs_manager.sbatch_stats_psv())

        sbatch_log_regex = work_exp_fs_manager.sbatch_file_regex(job_id)
        for slurm_log_file in sbatch_log_regex.parent.glob(sbatch_log_regex.name):
            if slurm_log_file.exists():
                shutil.copy(slurm_log_file, sample_fs_manager.sample_dir())
                slurm_log_file.unlink()

    if not any(work_exp_fs_manager.tmp_slurm_logs_dir().iterdir()):
        work_exp_fs_manager.tmp_slurm_logs_dir().rmdir()


def _move_work_to_data(
    work_exp_fs_manager: exp_fs.WorkManager,
    data_exp_fs_manager: exp_fs.DataManager,
    samples_to_run: list[smp_fs.RowNumberedItem],
) -> None:
    """Move work to data."""
    _LOGGER.info("Moving results to data directory")
    #
    # Move experiment configuration if does not yet exists
    #
    if not data_exp_fs_manager.config_yaml().exists():
        shutil.copy(
            work_exp_fs_manager.config_yaml(),
            data_exp_fs_manager.config_yaml(),
        )
    work_exp_fs_manager.config_yaml().unlink()
    #
    # Move experiment date
    #
    data_exp_fs_manager.date_txt().unlink(missing_ok=True)
    shutil.copy(work_exp_fs_manager.date_txt(), data_exp_fs_manager.date_txt())
    work_exp_fs_manager.date_txt().unlink()
    #
    # Move all run samples dirs
    #
    for run_sample in samples_to_run:
        work_sample_fs_manager = work_exp_fs_manager.sample_fs_manager(
            run_sample.item(),
        )
        data_sample_fs_manager = data_exp_fs_manager.sample_fs_manager(
            run_sample.item(),
        )
        shutil.rmtree(data_sample_fs_manager.sample_dir(), ignore_errors=True)
        shutil.copytree(
            work_sample_fs_manager.sample_dir(),
            data_sample_fs_manager.sample_dir(),
        )
        shutil.rmtree(work_sample_fs_manager.sample_dir(), ignore_errors=True)
    #
    # Move experiment scripts
    #
    data_exp_fs_manager.scripts_dir().mkdir(parents=True, exist_ok=True)
    for script_file in (
        work_exp_fs_manager.sbatch_sh_script(),
        work_exp_fs_manager.command_sh_script(),
    ):
        if script_file.exists():
            shutil.copy(script_file, data_exp_fs_manager.scripts_dir())
            script_file.unlink()
    #
    # Move experiment errors
    #
    data_exp_fs_manager.errors_tsv().unlink(missing_ok=True)
    if work_exp_fs_manager.errors_tsv().exists():
        shutil.copy(
            work_exp_fs_manager.errors_tsv(),
            data_exp_fs_manager.errors_tsv(),
        )
        work_exp_fs_manager.errors_tsv().unlink()
    #
    # Try to remove empty tree
    #
    tree_to_remove = [
        work_exp_fs_manager.root_dir(),
        work_exp_fs_manager.topic_dir(),
        work_exp_fs_manager.tool_dir(),
        work_exp_fs_manager.exp_dir(),
        work_exp_fs_manager.scripts_dir(),
    ]
    last_empty = True
    while tree_to_remove and last_empty:
        dir_to_remove = tree_to_remove.pop()
        if not any(dir_to_remove.iterdir()):
            dir_to_remove.rmdir()
        else:
            last_empty = False
