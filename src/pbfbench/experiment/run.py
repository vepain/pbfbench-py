"""Experiment run module."""

from __future__ import annotations

import logging
import shutil
from collections.abc import Callable

import typer

import pbfbench.abc.tool.connector as abc_tool_connector
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.missing_inputs as smp_miss_in
import pbfbench.samples.status as smp_status

from . import checks as exp_checks
from . import complete as exp_complete
from . import errors as exp_errors
from . import file_system as exp_fs
from . import iter as exp_iter
from . import managers as exp_managers

_LOGGER = logging.getLogger(__name__)


def start_new_experiment(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    target_samples_filter: Callable[[smp_status.Status], bool],
    format_inputs_fn: Callable[[exp_managers.WithArguments], None],
    slurm_opts: str,
) -> None:
    """Run the experiment."""
    # REFACTOR use markdown print and do better app prints

    _LOGGER.info(
        "Running experiment `%s` with tool `%s` for the topic `%s`.",
        exp_manager.exp_name(),
        exp_manager.tool_connector().description().name(),
        exp_manager.tool_connector().description().topic().name(),
    )

    _reset_experiment_working_directory(exp_manager)

    _first_experiment_run_or_check_same_config(exp_manager)

    samples_to_run = _get_samples_to_run(exp_manager, target_samples_filter)

    _LOGGER.info("Number of samples to run: %d", len(samples_to_run))

    _remove_from_previous_error_list_samples_to_run(exp_manager, samples_to_run)

    match exp_manager:
        case exp_managers.WithArguments():
            samples_to_run = _filter_missing_inputs(exp_manager, samples_to_run)

            format_inputs_fn(exp_manager)

    _manage_samples_to_send_to_sbatch(exp_manager, samples_to_run)

    # FIXME add this to print end stats functions
    # if run_stats.samples_with_errors():
    #     _LOGGER.info(
    #         "The list of samples which exit with errors is written to file: %s",
    #         data_exp_fs_manager.errors_tsv(),
    #     )


def _reset_experiment_working_directory(exp_manager: exp_managers.WithOptions) -> None:
    """Reset experiment working directory."""
    if exp_manager.work_fs_manager().exp_dir().exists():
        _LOGGER.info(
            "Removing experiment working directory: %s",
            exp_manager.work_fs_manager().exp_dir(),
        )
        shutil.rmtree(exp_manager.work_fs_manager().exp_dir())
    exp_manager.work_fs_manager().exp_dir().mkdir(parents=True)


def _first_experiment_run_or_check_same_config(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> None:
    """Check if the experiment has been run before and check the configs."""
    if exp_manager.data_fs_manager().history_yaml().exists():
        match exp_checks.compare_config_vs_config_in_data(
            exp_manager.tool_connector(),
            exp_manager.data_fs_manager().config_yaml(),  # must also exist
        ):
            case exp_checks.DifferentExperimentConfigs():
                raise typer.Exit(1)
    else:
        exp_manager.data_fs_manager().exp_dir().mkdir(parents=True, exist_ok=True)
        # Copy config files
        exp_manager.tool_connector().to_config().to_yaml(
            exp_manager.data_fs_manager().config_yaml(),
        )
        exp_manager.tool_connector().to_config().to_yaml(
            exp_manager.work_fs_manager().config_yaml(),
        )
        # Create scripts directory
        exp_manager.data_fs_manager().scripts_fs_manager().scripts_dir().mkdir(
            parents=True,
            exist_ok=True,
        )


def _get_samples_to_run(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    target_samples_filter: Callable[[smp_status.Status], bool],
) -> list[smp_fs.RowNumberedItem]:
    """Get samples to run."""
    return [
        row_numbered_item
        for row_numbered_item, status in exp_iter.samples_with_status(
            exp_manager.data_fs_manager(),
        )
        if target_samples_filter(status)
    ]


def _remove_from_previous_error_list_samples_to_run(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    samples_to_run: list[smp_fs.RowNumberedItem],
) -> None:
    """Remove from previous error list samples to run."""
    if not exp_manager.data_fs_manager().errors_tsv().exists():
        return

    sample_ids_to_run = {
        row_numbered_item.item().exp_sample_id() for row_numbered_item in samples_to_run
    }

    with exp_errors.ErrorsTSVReader.open(
        exp_manager.data_fs_manager().errors_tsv(),
    ) as errors_tsv_reader:
        to_keep_in_list = [
            sample_error
            for sample_error in errors_tsv_reader
            if sample_error.exp_sample_id() not in sample_ids_to_run
        ]
    with exp_errors.ErrorsTSVWriter.open(
        exp_manager.data_fs_manager().errors_tsv(),
        "w",
    ) as errors_tsv_writer:
        errors_tsv_writer.write_error_samples(to_keep_in_list)


def _filter_missing_inputs(
    exp_manager: exp_managers.WithArguments,
    samples_to_run: list[smp_fs.RowNumberedItem],
) -> list[smp_fs.RowNumberedItem]:
    """Filter missing inputs."""
    checked_samples_to_run: list[smp_fs.RowNumberedItem] = []
    samples_with_missing_inputs: list[smp_fs.RowNumberedItem] = []

    tool_inputs = dict(
        exp_manager.tool_connector()
        .arguments()
        .results(
            exp_manager.data_fs_manager(),
        ),
    )

    for row_numbered_sample in samples_to_run:
        sample_missing_inputs = smp_miss_in.sample_list(
            tool_inputs,
            row_numbered_sample.item(),
            exp_manager.tool_connector(),
        )

        if sample_missing_inputs:
            samples_with_missing_inputs.append(row_numbered_sample)
            smp_miss_in.write_sample_missing_inputs(
                exp_manager,
                row_numbered_sample,
                sample_missing_inputs,
            )
        else:
            checked_samples_to_run.append(row_numbered_sample)

    _write_experiment_missing_inputs(
        samples_with_missing_inputs,
        exp_manager.data_fs_manager(),
    )

    return checked_samples_to_run


def _write_experiment_missing_inputs(
    samples_with_missing_inputs: list[smp_fs.RowNumberedItem],
    data_exp_fs_manager: exp_fs.DataManager,
) -> None:
    """Write experiment missing inputs."""
    _LOGGER.error("Samples with missing inputs: %d", len(samples_with_missing_inputs))

    if not samples_with_missing_inputs:
        return

    with exp_errors.ErrorsTSVWriter.open(
        data_exp_fs_manager.errors_tsv(),
        "w",
    ) as out_exp_errors:
        out_exp_errors.write_error_samples(
            (
                exp_errors.SampleError.sample_item_with_missing_inputs(
                    row_numbered_item.item(),
                )
                for row_numbered_item in samples_with_missing_inputs
            ),
        )


def _manage_samples_to_send_to_sbatch(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    samples_to_run: list[smp_fs.RowNumberedItem],
) -> None:
    """Manage samples to send to sbatch."""
    if not samples_to_run:
        _LOGGER.info("No samples to run")
        return

    _LOGGER.info(
        "Number of samples sent to sbatch: %d",
        len(samples_to_run),
    )

    _prepare_work_dirs(exp_manager)

    _refresh_data_date(
        exp_manager.data_fs_manager(),
        exp_manager.work_fs_manager(),
    )  # FIXME move it, prehaps will change

    _create_and_run_sbatch_script(
        exp_manager.tool_connector(),
        samples_to_run,
        exp_manager.data_fs_manager(),
        exp_manager.work_fs_manager(),
    )

    exp_complete.complete_experiment(
        samples_to_run,
        exp_manager.data_fs_manager(),
        exp_manager.work_fs_manager(),
    )

    # FIXME use in print stats end function
    # if run_stats.samples_with_errors():
    #     _LOGGER.error(
    #         "Samples with errors: %d",
    #         len(run_stats.samples_with_errors()),
    #     )


def _prepare_work_dirs(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
) -> None:
    """Prepare experiment file systems."""
    shutil.rmtree(exp_manager.work_fs_manager().exp_dir(), ignore_errors=True)
    exp_manager.work_fs_manager().exp_dir().mkdir(parents=True, exist_ok=True)

    # Create date file
    # with exp_manager.work_fs_manager().date_txt().open("w") as f_out:
    #     f_out.write(exp_manager.work_fs_manager().date_str() + "\n")

    exp_manager.tool_connector().to_config().to_yaml(
        exp_manager.work_fs_manager().config_yaml(),
    )
    exp_manager.work_fs_manager().scripts_fs_manager().scripts_dir().mkdir(
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
    tool_connector: abc_tool_connector.WithOptions,
    checked_inputs_samples_to_run: list[smp_fs.RowNumberedItem],
    data_exp_fs_manager: exp_fs.DataManager,
    work_exp_fs_manager: exp_fs.WorkManager,
) -> None:
    """Run sbatch script."""
    # sbatch_script = exp_bash_create.run_scripts(
    #     data_exp_fs_manager,
    #     work_exp_fs_manager,
    #     checked_inputs_samples_to_run,
    #     exp_config,
    #     tool_connector,
    # )

    # cmd_path = subprocess_lib.command_path(slurm_bash.SBATCH_CMD)
    # result = subprocess.run(
    #     [str(x) for x in [cmd_path, sbatch_script]],
    #     capture_output=True,
    #     text=True,
    #     check=False,
    # )
    # # FIXME should check and return Error if failed
    # _LOGGER.debug("%s stdout: %s", slurm_bash.SBATCH_CMD, result.stdout)
    # _LOGGER.debug("%s stderr: %s", slurm_bash.SBATCH_CMD, result.stderr)
