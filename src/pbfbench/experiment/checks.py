"""Experiment checking module."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import TYPE_CHECKING

import pbfbench.abc.tool.config as abc_tool_cfg
import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.abc.topic.results.items as abc_topic_res_items
import pbfbench.experiment.config as exp_cfg
import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.items as smp_items
import pbfbench.samples.missing_inputs as smp_miss_in
import pbfbench.samples.status as smp_status

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

_LOGGER = logging.getLogger(__name__)


def exists(data_manager: exp_fs.Manager) -> bool:
    """Check if experiment exists."""
    return data_manager.config_yaml().exists()


class SameExperimentError(StrEnum):
    """Same experiment error."""

    DIFFERENT_SYNTAX = "different_syntax"
    NOT_SAME = "not_same"


def check_config_inputs(
    config: exp_cfg.Config,
    connector: abc_tool_visitor.Connector,
) -> bool:
    """Check config inputs."""
    value_errors = connector.check_arguments_implement_results(config)
    for value_error in value_errors:
        _LOGGER.critical(str(value_error))
    return not value_errors


def is_same_experiment[C: exp_cfg.Config](
    data_fs_manager: exp_fs.Manager,
    config: C,
) -> None | SameExperimentError:
    """Check if experiment is the same."""
    try:
        config_in_data: C = type(config).from_yaml(
            data_fs_manager.config_yaml(),
        )
    except Exception:  # noqa: BLE001
        return SameExperimentError.DIFFERENT_SYNTAX

    if not config.is_same(config_in_data):
        return SameExperimentError.NOT_SAME

    return None


def samples_with_error_status(
    data_manager: exp_fs.Manager,
    all_samples: Iterable[smp_fs.RowNumberedItem],
) -> Iterator[smp_fs.RowNumberedItem]:
    """Get samples with error status.

    They correspond to samples for which the experiment is not done.
    """
    return (
        row_numbered_sample
        for row_numbered_sample in all_samples
        if smp_status.get_status(
            data_manager.sample_fs_manager(row_numbered_sample.item()),
        )
        != smp_status.OKStatus.OK
    )


def samples_to_format_result(
    data_manager: exp_fs.Manager,
    all_samples: Iterable[smp_fs.RowNumberedItem],
    fn_format_result_exists: Callable[[exp_fs.Manager, smp_items.Item], bool],
) -> Iterator[smp_fs.RowNumberedItem]:
    """Get samples to format result.

    They correspond to samples for which the experiment is done
    but the result is not formatted for the current tool.
    """
    # FIXME this will change, refactor to follow the same structure as above
    return (
        row_numbered_sample
        for row_numbered_sample in all_samples
        if fn_format_result_exists(data_manager, row_numbered_sample.item())
    )


# REFACTOR move to samples module
def checked_input_samples_to_run(
    work_exp_fs_manager: exp_fs.Manager,
    samples_to_run: Iterable[smp_fs.RowNumberedItem],
    tool_inputs: dict[abc_tool_cfg.Names, abc_topic_res_items.Result],
) -> tuple[list[smp_fs.RowNumberedItem], list[smp_fs.RowNumberedItem]]:
    """Return row numbered samples to run and those with missing inputs."""
    checked_samples_to_run: list[smp_fs.RowNumberedItem] = []
    samples_with_missing_inputs: list[smp_fs.RowNumberedItem] = []

    for row_numbered_sample in samples_to_run:
        sample_missing_inputs = missing_inputs(
            tool_inputs,
            row_numbered_sample.item(),
        )

        if sample_missing_inputs:
            samples_with_missing_inputs.append(row_numbered_sample)
            sample_fs_manager = work_exp_fs_manager.sample_fs_manager(
                row_numbered_sample.item(),
            )
            smp_miss_in.write_sample_missing_inputs(
                sample_fs_manager,
                sample_missing_inputs,
            )
        else:
            checked_samples_to_run.append(row_numbered_sample)

    return checked_samples_to_run, samples_with_missing_inputs


def missing_inputs[N: abc_tool_cfg.Names](
    tool_inputs: dict[N, abc_topic_res_items.Result],
    sample_item: smp_items.Item,
) -> list[smp_miss_in.MissingInput]:
    """Check input(s) and return True if OK, False otherwise.

    In case the input is missing or not valid, it logs a helper message.
    """
    list_missing_inputs: list[smp_miss_in.MissingInput] = []
    for arg_name, tool_input in tool_inputs.items():
        input_status = tool_input.check(sample_item)
        if isinstance(input_status, smp_status.ErrorStatus):
            missing_input = smp_miss_in.MissingInput.from_tool_input(
                str(arg_name),
                tool_input,
                input_status,
            )
            list_missing_inputs.append(missing_input)
    return list_missing_inputs
