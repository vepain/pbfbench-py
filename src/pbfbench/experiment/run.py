"""Experiment run module."""

from __future__ import annotations

import logging
import shutil
from typing import TYPE_CHECKING, cast

import typer

import pbfbench.abc.tool.connector as abc_tool_connector
import pbfbench.abc.topic.results as abc_topic_res
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.missing_inputs as smp_miss_in
import pbfbench.samples.status as smp_status

from . import checks as exp_checks
from . import errors as exp_errors
from . import file_system as exp_fs
from . import history, in_progress, monitors
from . import iter as exp_iter
from . import managers as exp_managers
from .bash import create as exp_bash_create
from .slurm import run as exp_slurm_run

if TYPE_CHECKING:
    from collections.abc import Callable

_LOGGER = logging.getLogger(__name__)


def start_new_experiment(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    target_samples_filter: Callable[[smp_status.Status], bool],
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
    if not samples_to_run:
        _LOGGER.info("No samples to run")
        return

    if isinstance(exp_manager, exp_managers.WithArguments):
        samples_to_run = _manage_inputs(exp_manager, samples_to_run)

    if not samples_to_run:
        _LOGGER.info("No samples to run")
        history.update_history(exp_manager)
        return

    _LOGGER.info(
        "Number of samples sent to sbatch: %d",
        len(samples_to_run),
    )

    sh_manager = exp_bash_create.run_scripts(
        exp_manager,
        samples_to_run,
        slurm_opts,
    )

    exp_slurm_run.run(exp_manager, sh_manager)
    in_progress.write_in_progress_metadata(exp_manager, sh_manager)

    # exp_complete.complete_experiment(
    #     samples_to_run,
    #     exp_manager.data_fs_manager(),
    #     exp_manager.work_fs_manager(),
    # )


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


def _get_samples_to_run(
    exp_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    target_samples_filter: Callable[[smp_status.Status], bool],
) -> list[smp_fs.RowNumberedItem]:
    """Get samples to run."""
    samples_to_run = [
        row_numbered_item
        for row_numbered_item, status in exp_iter.samples_with_status(
            exp_manager.data_fs_manager(),
        )
        if target_samples_filter(status)
    ]
    _LOGGER.info("Number of samples to run: %d", len(samples_to_run))

    _remove_from_previous_error_list_samples_to_run(exp_manager, samples_to_run)

    monitors.write_unresolved_samples(exp_manager.work_fs_manager(), samples_to_run)

    return samples_to_run


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


def _manage_inputs(
    exp_manager: exp_managers.WithArguments,
    samples_to_run: list[smp_fs.RowNumberedItem],
) -> list[smp_fs.RowNumberedItem]:
    """Manage inputs."""
    _format_inputs(exp_manager, samples_to_run)
    return _filter_missing_inputs(exp_manager, samples_to_run)


def _format_inputs[N: abc_tool_connector.Names](
    exp_manager: exp_managers.WithArguments[N],
    samples_to_run: list[smp_fs.RowNumberedItem],
) -> None:
    tool_inputs_to_fmt: list[tuple[exp_fs.DataManager, abc_topic_res.ConvertFn]] = []
    missing_convert_fn = False
    for _, arg in exp_manager.tool_connector().arguments():
        result_visitor = arg.result_visitor()
        if result_visitor is abc_topic_res.FormattedVisitor:
            result_visitor = cast(
                "type[abc_topic_res.FormattedVisitor]",
                result_visitor,
            )
            convert_fn_or_err = result_visitor.convert_fn(arg.tool())
            if isinstance(convert_fn_or_err, abc_topic_res.Error):
                _LOGGER.critical("%s", convert_fn_or_err)
                missing_convert_fn = True
                continue

            in_data_exp_fs_manager = exp_fs.DataManager(
                exp_manager.data_fs_manager().root_dir(),
                arg.tool().to_description(),
                arg.exp_name(),
            )

            tool_inputs_to_fmt.append((in_data_exp_fs_manager, convert_fn_or_err))

    if missing_convert_fn:
        return

    for row_numbered_sample in samples_to_run:
        for in_data_exp_fs_manager, convert_fn in tool_inputs_to_fmt:
            # OPTIMIZE do not redo format if exists?
            try:
                convert_fn(in_data_exp_fs_manager, row_numbered_sample.item())
            except Exception:
                _LOGGER.exception(
                    "Error formatting sample %s",
                    row_numbered_sample.item().exp_sample_id(),
                )


def _filter_missing_inputs[N: abc_tool_connector.Names](
    exp_manager: exp_managers.WithArguments[N],
    samples_to_run: list[smp_fs.RowNumberedItem],
) -> list[smp_fs.RowNumberedItem]:
    """Filter missing inputs."""
    if not samples_to_run:
        return []

    samples_without_missing_inputs: list[smp_fs.RowNumberedItem] = []
    samples_with_missing_inputs: list[smp_fs.RowNumberedItem] = []

    tool_inputs = dict(
        exp_manager.tool_connector().arguments().results(exp_manager.data_fs_manager()),
    )

    for row_numbered_sample in samples_to_run:
        sample_missing_inputs = smp_miss_in.for_sample(
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
            samples_without_missing_inputs.append(row_numbered_sample)

    if samples_with_missing_inputs:
        _LOGGER.error(
            "Samples with missing inputs: %d",
            len(samples_with_missing_inputs),
        )
        exp_errors.write_missing_inputs(
            exp_manager.data_fs_manager(),
            samples_with_missing_inputs,
        )
        monitors.update_samples_resolution_status(
            exp_manager.work_fs_manager(),
            ((s, smp_status.Error.MISSING_INPUTS) for s in samples_with_missing_inputs),
        )

    return samples_without_missing_inputs


# FIXME WORK IN PROGRESS ---
