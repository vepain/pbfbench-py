"""Experiment run module."""

from __future__ import annotations

import logging
import shutil
import subprocess

import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.experiment.bash.create as exp_bash
import pbfbench.experiment.complete as exp_complete
import pbfbench.experiment.config as exp_cfg
import pbfbench.experiment.errors as exp_errors
import pbfbench.experiment.file_system as exp_fs
import pbfbench.experiment.iter as exp_iter
import pbfbench.experiment.stats as exp_stats
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.status as smp_status
import pbfbench.slurm.bash as slurm_bash
from pbfbench import subprocess_lib

_LOGGER = logging.getLogger(__name__)


def run_experiment_on_samples_only_options(
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
    exp_config: exp_cfg.ConfigOnlyOptions,
    tool_connector: abc_tool_visitor.ConnectorOnlyOptions,
) -> exp_stats.RunStatsOnlyOptions:
    """Run the experiment."""
    # REFACTOR use markdown print and do better app prints

    _LOGGER.info(
        "Running experiment `%s` with tool `%s` for the topic `%s`.",
        exp_config.name(),
        tool_connector.description().name(),
        tool_connector.description().topic().name(),
    )

    _prepare_data_dirs(data_exp_fs_manager, exp_config)

    run_stats = exp_stats.RunStatsOnlyOptions.new(data_exp_fs_manager)

    samples_to_run = _get_samples_to_run(data_exp_fs_manager, run_stats)

    _manage_samples_to_send_to_sbatch(
        samples_to_run,
        data_exp_fs_manager,
        work_exp_fs_manager,
        exp_config,
        tool_connector,
        run_stats,
    )

    if run_stats.samples_with_errors():
        _LOGGER.info(
            "The list of samples which exit with errors is written to file: %s",
            data_exp_fs_manager.errors_tsv(),
        )

    return run_stats


def run_experiment_on_samples_with_arguments(
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
    exp_config: exp_cfg.ConfigWithArguments,
    tool_connector: abc_tool_visitor.ConnectorWithArguments,
) -> exp_stats.RunStatsWithArguments:
    """Run the experiment."""
    # REFACTOR use markdown print and do better app prints

    _LOGGER.info(
        "Running experiment `%s` with tool `%s` for the topic `%s`.",
        exp_config.name(),
        tool_connector.description().name(),
        tool_connector.description().topic().name(),
    )

    _prepare_data_dirs(data_exp_fs_manager, exp_config)

    run_stats = exp_stats.RunStatsWithArguments.new(data_exp_fs_manager)

    samples_to_run = _get_samples_to_run(data_exp_fs_manager, run_stats)

    checked_inputs_samples_to_run, samples_with_missing_inputs = _filter_missing_inputs(
        tool_connector,
        exp_config,
        samples_to_run,
        data_exp_fs_manager,
        work_exp_fs_manager,
    )

    # FIXME if complete and work dir exist, verify also work config file

    _write_experiment_missing_inputs(
        samples_with_missing_inputs,
        data_exp_fs_manager,
        run_stats,
    )

    _manage_samples_to_send_to_sbatch(
        checked_inputs_samples_to_run,
        data_exp_fs_manager,
        work_exp_fs_manager,
        exp_config,
        tool_connector,
        run_stats,
    )

    if run_stats.samples_with_missing_inputs() or run_stats.samples_with_errors():
        _LOGGER.info(
            "The list of samples with missing inputs"
            " or which exit with errors is written to file: %s",
            data_exp_fs_manager.errors_tsv(),
        )

    return run_stats


def _prepare_data_dirs(
    data_exp_fs_manager: exp_fs.DataManager,
    exp_config: exp_cfg.ConfigWithOptions,
) -> None:
    """Reset experiment errors."""
    data_exp_fs_manager.exp_dir().mkdir(parents=True, exist_ok=True)
    data_exp_fs_manager.errors_tsv().unlink(missing_ok=True)

    exp_config.to_yaml(data_exp_fs_manager.config_yaml())
    data_exp_fs_manager.scripts_fs_manager().scripts_dir().mkdir(
        parents=True,
        exist_ok=True,
    )


def _get_samples_to_run(
    data_exp_fs_manager: exp_fs.DataManager,
    run_stats: exp_stats.RunStatsWithOptions,
) -> list[smp_fs.RowNumberedItem]:
    """Get samples to run."""
    with smp_fs.TSVReader.open(data_exp_fs_manager.samples_tsv()) as smp_tsv_in:
        samples_to_run = list(
            exp_iter.samples_to_run(
                data_exp_fs_manager,
                smp_tsv_in.iter_row_numbered_items(),
            ),
        )
    run_stats.add_samples_to_run(len(samples_to_run))

    _LOGGER.info("Number of samples to run: %d", len(samples_to_run))

    return samples_to_run


def _filter_missing_inputs(
    tool_connector: abc_tool_visitor.ConnectorWithArguments,
    exp_config: exp_cfg.ConfigWithArguments,
    samples_to_run: list[smp_fs.RowNumberedItem],
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
) -> tuple[
    list[smp_fs.RowNumberedItem],
    list[smp_fs.RowNumberedItem],
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
            tool_connector,
        )
    )

    return (
        checked_inputs_samples_to_run,
        samples_with_missing_inputs,
    )


def _write_experiment_missing_inputs(
    samples_with_missing_inputs: list[smp_fs.RowNumberedItem],
    data_exp_fs_manager: exp_fs.DataManager,
    run_stats: exp_stats.RunStatsWithArguments,
) -> None:
    """Write experiment missing inputs."""
    run_stats.samples_with_missing_inputs().extend(
        sample.item().exp_sample_id() for sample in samples_with_missing_inputs
    )

    _LOGGER.error("Samples with missing inputs: %d", len(samples_with_missing_inputs))

    if not samples_with_missing_inputs:
        return

    with exp_errors.ErrorsTSVWriter.open(
        data_exp_fs_manager.errors_tsv(),
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


def _manage_samples_to_send_to_sbatch(  # noqa: PLR0913
    samples_to_run: list[smp_fs.RowNumberedItem],
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
    exp_config: exp_cfg.ConfigWithOptions,
    tool_connector: abc_tool_visitor.ConnectorWithOptions,
    run_stats: exp_stats.RunStatsWithOptions,
) -> None:
    """Manage samples to send to sbatch."""
    if not samples_to_run:
        _LOGGER.info("No samples to run")
        return

    _LOGGER.info(
        "Number of samples sent to sbatch: %d",
        len(samples_to_run),
    )

    _prepare_work_dirs(work_exp_fs_manager, exp_config)
    _refresh_data_date(data_exp_fs_manager, work_exp_fs_manager)

    _create_and_run_sbatch_script(
        tool_connector,
        exp_config,
        samples_to_run,
        data_exp_fs_manager,
        work_exp_fs_manager,
    )

    exp_complete.complete_experiment(
        samples_to_run,
        data_exp_fs_manager,
        work_exp_fs_manager,
        run_stats,
    )

    if run_stats.samples_with_errors():
        _LOGGER.error(
            "Samples with errors: %d",
            len(run_stats.samples_with_errors()),
        )


def _prepare_work_dirs(
    work_exp_fs_manager: exp_fs.WorkManager,
    exp_config: exp_cfg.ConfigWithOptions,
) -> None:
    """Prepare experiment file systems."""
    shutil.rmtree(work_exp_fs_manager.exp_dir(), ignore_errors=True)
    work_exp_fs_manager.exp_dir().mkdir(parents=True, exist_ok=True)

    # Create date file
    with work_exp_fs_manager.date_txt().open("w") as f_out:
        f_out.write(work_exp_fs_manager.date_str() + "\n")

    exp_config.to_yaml(work_exp_fs_manager.config_yaml())
    work_exp_fs_manager.scripts_fs_manager().scripts_dir().mkdir(
        parents=True,
        exist_ok=True,
    )


def _refresh_data_date(
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
) -> None:
    data_exp_fs_manager.date_txt().unlink(missing_ok=True)
    shutil.copy(work_exp_fs_manager.date_txt(), data_exp_fs_manager.date_txt())


def _create_and_run_sbatch_script(
    tool_connector: abc_tool_visitor.ConnectorWithOptions,
    exp_config: exp_cfg.ConfigWithOptions,
    checked_inputs_samples_to_run: list[smp_fs.RowNumberedItem],
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
) -> None:
    """Run sbatch script."""
    sbatch_script = exp_bash.run_scripts(
        data_exp_fs_manager,
        work_exp_fs_manager,
        checked_inputs_samples_to_run,
        exp_config,
        tool_connector,
    )

    cmd_path = subprocess_lib.command_path(slurm_bash.SBATCH_CMD)
    result = subprocess.run(  # noqa: S603
        [str(x) for x in [cmd_path, sbatch_script]],
        capture_output=True,
        text=True,
        check=False,
    )
    # FIXME should check and return Error if failed
    _LOGGER.debug("%s stdout: %s", slurm_bash.SBATCH_CMD, result.stdout)
    _LOGGER.debug("%s stderr: %s", slurm_bash.SBATCH_CMD, result.stderr)
