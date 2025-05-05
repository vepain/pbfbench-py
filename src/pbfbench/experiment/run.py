"""Experiment run module."""

from __future__ import annotations

import logging
import shutil
import time
from enum import StrEnum
from typing import TYPE_CHECKING

import rich.progress as rich_prog

import pbfbench.abc.tool.config as abc_tool_cfg
import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.abc.topic.results.items as abc_topic_results
import pbfbench.experiment.checks as exp_checks
import pbfbench.experiment.config as exp_cfg
import pbfbench.experiment.errors as exp_errors
import pbfbench.experiment.file_system as exp_fs
import pbfbench.experiment.shell as exp_shell
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.status as smp_status
from pbfbench import root_logging, slurm, subprocess_lib

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


_LOGGER = logging.getLogger(__name__)


class RunStats:
    """Experiment run stats."""

    @classmethod
    def new(cls, data_exp_fs_manager: exp_fs.Manager) -> RunStats:
        """Create new run stats."""
        with smp_fs.TSVReader.open(
            smp_fs.samples_tsv(data_exp_fs_manager.root_dir()),
        ) as smp_tsv_in:
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


class ErrorStatus(StrEnum):
    """Experiment error status."""

    NO_WRITE_ACCESS = "no_write_access"
    NO_READ_ACCESS = "no_read_access"
    NO_TOOL_ENV_WRAPPER_SCRIPT = "no_tool_env_wrapper_script"
    WRONG_EXPERIMENT_CONFIG_SYNTAX = "wrong_experiment_config_syntax"
    DIFFERENT_EXPERIMENT = "different_experiment"


type Status = RunStats | ErrorStatus


def run_experiment_on_samples(
    data_dir: Path,
    working_dir: Path,
    exp_config_yaml: Path,
    tool_connector: abc_tool_visitor.Connector,
) -> Status:
    """Run the experiment."""
    rw_check_result = _check_read_write_access(data_dir, working_dir)
    if rw_check_result is not None:
        return rw_check_result

    try:
        exp_config = tool_connector.read_config(exp_config_yaml)
    except Exception:  # noqa: BLE001
        return ErrorStatus.WRONG_EXPERIMENT_CONFIG_SYNTAX

    _log_config(exp_config, tool_connector)

    match preparation_result := _prepare_experiment_file_systems(
        data_dir,
        working_dir,
        tool_connector,
        exp_config,
    ):
        case ErrorStatus():
            return preparation_result
        case _:
            data_exp_fs_manager, working_exp_fs_manager = preparation_result

    run_stats = RunStats.new(data_exp_fs_manager)

    samples_to_run = _get_samples_to_run(data_exp_fs_manager, run_stats)

    _prepare_sample_directories(samples_to_run, working_exp_fs_manager)

    checked_inputs_samples_to_run, samples_with_missing_inputs, tool_inputs = (
        _filter_missing_inputs(
            tool_connector,
            exp_config,
            samples_to_run,
            data_exp_fs_manager,
            working_exp_fs_manager,
        )
    )

    _write_experiment_missing_inputs(
        samples_with_missing_inputs,
        working_exp_fs_manager,
        run_stats,
    )

    if not checked_inputs_samples_to_run:
        _LOGGER.info("No samples to run")
        return run_stats

    _create_and_run_sbatch_script(
        tool_connector,
        tool_inputs,
        exp_config,
        checked_inputs_samples_to_run,
        data_exp_fs_manager,
        working_exp_fs_manager,
    )

    _wait_all_job_finish(checked_inputs_samples_to_run, working_exp_fs_manager)

    _write_experiment_errors(
        checked_inputs_samples_to_run,
        working_exp_fs_manager,
        run_stats,
    )

    _write_sbatch_stats_and_move_slurm_logs(
        checked_inputs_samples_to_run,
        working_exp_fs_manager,
    )

    _move_work_to_data(
        working_exp_fs_manager,
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


def _check_read_write_access(data_dir: Path, working_dir: Path) -> None | ErrorStatus:
    """Check read and write access."""
    #
    # Check read/write access to data_dir and working_dir
    #
    try:
        working_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        _LOGGER.critical("No write access to %s", working_dir)
        return ErrorStatus.NO_WRITE_ACCESS

    for test_dir in (data_dir, working_dir):
        file_test = test_dir / "test_read_write.txt"
        try:
            file_test.write_text("test")
        except OSError:
            _LOGGER.critical("No write access to %s", test_dir)
            return ErrorStatus.NO_WRITE_ACCESS
        try:
            file_test.read_text()
        except OSError:
            _LOGGER.critical("No read access to %s", test_dir)
            file_test.unlink()
            return ErrorStatus.NO_READ_ACCESS
        file_test.unlink()

    return None


def _log_config(
    exp_config: exp_cfg.Config,
    tool_connector: abc_tool_visitor.Connector,
) -> None:
    """Log config."""
    _LOGGER.info(
        "Running experiment %s with tool %s for the topic %s.",
        exp_config.name(),
        tool_connector.tool_description().name(),
        tool_connector.tool_description().topic().name(),
    )
    _LOGGER.debug("Experiment config:\n%s", exp_config.to_yaml_dump())


def _prepare_experiment_file_systems[C: exp_cfg.Config](
    data_dir: Path,
    working_dir: Path,
    tool_connector: abc_tool_visitor.Connector,
    exp_config: C,
) -> ErrorStatus | tuple[exp_fs.Manager, exp_fs.Manager]:
    """Prepare experiment file systems."""
    data_exp_fs_manager, working_exp_fs_manager = exp_fs.data_and_working_managers(
        data_dir,
        working_dir,
        tool_connector.tool_description(),
        exp_config.name(),
    )

    if not data_exp_fs_manager.tool_env_script_sh().exists():
        return ErrorStatus.NO_TOOL_ENV_WRAPPER_SCRIPT

    if exp_checks.exists(data_exp_fs_manager):
        same_exp_result = exp_checks.is_same_experiment(data_exp_fs_manager, exp_config)
        if same_exp_result is not None:
            match same_exp_result:
                case exp_checks.SameExperimentError.DIFFERENT_SYNTAX:
                    return ErrorStatus.WRONG_EXPERIMENT_CONFIG_SYNTAX
                case exp_checks.SameExperimentError.NOT_SAME:
                    return ErrorStatus.DIFFERENT_EXPERIMENT
    else:
        data_exp_fs_manager.exp_dir().mkdir(parents=True, exist_ok=True)
        exp_config.to_yaml(data_exp_fs_manager.config_yaml())

    shutil.rmtree(working_exp_fs_manager.exp_dir(), ignore_errors=True)
    working_exp_fs_manager.exp_dir().mkdir(parents=True, exist_ok=True)
    exp_config.to_yaml(working_exp_fs_manager.config_yaml())
    working_exp_fs_manager.tmp_slurm_logs_dir().mkdir(parents=True, exist_ok=True)

    for fs_manager in (data_exp_fs_manager, working_exp_fs_manager):
        fs_manager.scripts_dir().mkdir(parents=True, exist_ok=True)

    return data_exp_fs_manager, working_exp_fs_manager


def _get_samples_to_run(
    data_exp_fs_manager: exp_fs.Manager,
    run_stats: RunStats,
) -> list[smp_fs.RowNumberedItem]:
    """Get samples to run."""
    with smp_fs.TSVReader.open(
        smp_fs.samples_tsv(data_exp_fs_manager.root_dir()),
    ) as smp_tsv_in:
        samples_to_run = list(
            exp_checks.samples_with_error_status(
                data_exp_fs_manager,
                smp_tsv_in.iter_row_numbered_items(),
            ),
        )
    run_stats.add_samples_to_run(len(samples_to_run))

    return samples_to_run


def _prepare_sample_directories(
    samples_to_run: Iterable[smp_fs.RowNumberedItem],
    working_exp_fs_manager: exp_fs.Manager,
) -> None:
    """Prepare sample directories."""
    for run_sample in samples_to_run:
        sample_fs_manager = working_exp_fs_manager.sample_fs_manager(run_sample.item())
        sample_fs_manager.sample_dir().mkdir(parents=True, exist_ok=True)


def _filter_missing_inputs(
    tool_connector: abc_tool_visitor.Connector,
    exp_config: exp_cfg.Config,
    samples_to_run: list[smp_fs.RowNumberedItem],
    data_exp_fs_manager: exp_fs.Manager,
    working_exp_fs_manager: exp_fs.Manager,
) -> tuple[
    list[smp_fs.RowNumberedItem],
    list[smp_fs.RowNumberedItem],
    dict[abc_tool_cfg.Names, abc_topic_results.Result],
]:
    """Filter missing inputs."""
    tool_inputs = tool_connector.config_to_inputs(exp_config, data_exp_fs_manager)

    checked_inputs_samples_to_run, samples_with_missing_inputs = (
        exp_checks.checked_input_samples_to_run(
            working_exp_fs_manager,
            samples_to_run,
            tool_inputs,
        )
    )

    return checked_inputs_samples_to_run, samples_with_missing_inputs, tool_inputs


def _write_experiment_missing_inputs(
    samples_with_missing_inputs: list[smp_fs.RowNumberedItem],
    working_exp_fs_manager: exp_fs.Manager,
    run_stats: RunStats,
) -> None:
    """Write experiment missing inputs."""
    run_stats.samples_with_missing_inputs().extend(
        sample.item().exp_sample_id() for sample in samples_with_missing_inputs
    )

    _LOGGER.error("Samples with missing inputs: %d", len(samples_with_missing_inputs))

    with exp_errors.ErrorsTSVWriter.open(
        working_exp_fs_manager.errors_tsv(),
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
    tool_inputs: dict[abc_tool_cfg.Names, abc_topic_results.Result],
    exp_config: exp_cfg.Config,
    checked_inputs_samples_to_run: list[smp_fs.RowNumberedItem],
    data_exp_fs_manager: exp_fs.Manager,
    working_exp_fs_manager: exp_fs.Manager,
) -> None:
    """Run sbatch script."""
    tool_commands = tool_connector.inputs_to_commands(
        exp_config,
        tool_inputs,
        working_exp_fs_manager,
    )
    exp_shell.create_run_script(
        data_exp_fs_manager,
        working_exp_fs_manager,
        checked_inputs_samples_to_run,
        exp_config.slurm_config(),
        tool_commands,
    )

    cmd_path = subprocess_lib.command_path(slurm.SBATCH_CMD)
    cli_line = [cmd_path, working_exp_fs_manager.sbatch_sh_script()]
    subprocess_lib.run_cmd(cli_line, slurm.SBATCH_CMD)


def _wait_all_job_finish(
    checked_inputs_samples_to_run: list[smp_fs.RowNumberedItem],
    working_exp_fs_manager: exp_fs.Manager,
) -> None:
    """Wait all job finish."""
    in_running_jobs = checked_inputs_samples_to_run.copy()

    with rich_prog.Progress(console=root_logging.CONSOLE) as progress:
        slurm_running_task = progress.add_task(
            "Slurm running",
            total=len(in_running_jobs),
        )
        while in_running_jobs:
            time.sleep(60)
            _tmp_running_jobs = []
            for job in in_running_jobs:
                sample_fs_manager = working_exp_fs_manager.sample_fs_manager(
                    job.item(),
                )
                if (
                    smp_status.get_status(sample_fs_manager)
                    == smp_status.ErrorStatus.NOT_RUN
                ):
                    _tmp_running_jobs.append(job)

            progress.update(
                slurm_running_task,
                advance=(len(in_running_jobs) - len(_tmp_running_jobs)),
            )
            in_running_jobs = _tmp_running_jobs


def _write_experiment_errors(
    run_samples: list[smp_fs.RowNumberedItem],
    working_exp_fs_manager: exp_fs.Manager,
    run_stats: RunStats,
) -> None:
    """Write experiment errors."""
    for run_sample in run_samples:
        sample_fs_manager = working_exp_fs_manager.sample_fs_manager(
            run_sample.item(),
        )
        if smp_status.get_status(sample_fs_manager) == smp_status.ErrorStatus.ERROR:
            run_stats.samples_with_errors().append(run_sample.item().exp_sample_id())

    _LOGGER.error("Samples with errors: %d", len(run_stats.samples_with_errors()))

    with exp_errors.ErrorsTSVWriter.open(
        working_exp_fs_manager.errors_tsv(),
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


def _write_sbatch_stats_and_move_slurm_logs(
    run_samples: list[smp_fs.RowNumberedItem],
    working_exp_fs_manager: exp_fs.Manager,
) -> None:
    """Write sbatch stats."""
    for run_sample in run_samples:
        sample_fs_manager = working_exp_fs_manager.sample_fs_manager(run_sample.item())
        job_id = smp_fs.get_job_id_from_file(sample_fs_manager)
        slurm.write_slurm_stats(job_id, sample_fs_manager.sbatch_stats_psv())

        for slurm_log_file in (
            slurm.out_log_path(working_exp_fs_manager, job_id),
            slurm.err_log_path(working_exp_fs_manager, job_id),
        ):
            shutil.move(slurm_log_file, sample_fs_manager.sample_dir())

    if not any(working_exp_fs_manager.tmp_slurm_logs_dir().iterdir()):
        working_exp_fs_manager.tmp_slurm_logs_dir().rmdir()


def _move_work_to_data(
    working_exp_fs_manager: exp_fs.Manager,
    data_exp_fs_manager: exp_fs.Manager,
    samples_to_run: list[smp_fs.RowNumberedItem],
) -> None:
    """Move work to data."""
    _LOGGER.info("Moving results to data directory")
    #
    # Move all run samples dirs
    #
    for run_sample in samples_to_run:
        work_sample_fs_manager = working_exp_fs_manager.sample_fs_manager(
            run_sample.item(),
        )
        data_sample_fs_manager = data_exp_fs_manager.sample_fs_manager(
            run_sample.item(),
        )
        shutil.rmtree(data_sample_fs_manager.sample_dir(), ignore_errors=True)
        shutil.move(
            work_sample_fs_manager.sample_dir(),
            data_sample_fs_manager.sample_dir(),
        )
    #
    # Move experiment scripts
    #
    for sh_script in (
        working_exp_fs_manager.sbatch_sh_script(),
        working_exp_fs_manager.command_sh_script(),
    ):
        shutil.move(sh_script, data_exp_fs_manager.scripts_dir())
    #
    # Move experiment errors
    #
    data_exp_fs_manager.errors_tsv().unlink(missing_ok=True)
    shutil.move(
        working_exp_fs_manager.errors_tsv(),
        data_exp_fs_manager.errors_tsv(),
    )
