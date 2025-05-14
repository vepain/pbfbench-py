"""Experiment iter module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pbfbench.abc.tool.config as abc_tool_cfg
import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.abc.topic.results.items as abc_topic_res_items
import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.missing_inputs as smp_miss_in
import pbfbench.samples.status as smp_status

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


def samples_to_run(
    data_exp_fs_manager: exp_fs.DataManager,
    all_samples: Iterable[smp_fs.RowNumberedItem],
) -> Iterator[smp_fs.RowNumberedItem]:
    """Get samples with error status.

    They correspond to samples for which the experiment is not done.
    """
    return (
        row_numbered_sample
        for row_numbered_sample in all_samples
        if smp_status.get_status(
            data_exp_fs_manager.sample_fs_manager(row_numbered_sample.item()),
        )
        != smp_status.OKStatus.OK
    )


def samples_to_format_result(
    formatted_result_builder: abc_topic_res_items.Formatted,
    all_samples: Iterable[smp_fs.RowNumberedItem],
) -> Iterator[smp_fs.RowNumberedItem]:
    """Get input samples to format result.

    They correspond to input samples for which the experiment is done
    but the result is not formatted for the current tool.
    """
    # TODO log that requires to run before init
    # TODO perhaps missing inputs for check should be good (I removed it...)
    done_input = (
        row_numbered_sample
        for row_numbered_sample in all_samples
        if smp_status.get_status(
            formatted_result_builder.exp_fs_manager().sample_fs_manager(
                row_numbered_sample.item(),
            ),
        )
        == smp_status.OKStatus.OK
    )
    return (
        row_numbered_sample
        for row_numbered_sample in done_input
        if formatted_result_builder.check(row_numbered_sample.item())
        != smp_status.OKStatus.OK
    )


def checked_input_samples_to_run(
    work_exp_fs_manager: exp_fs.WorkManager,
    samples_to_run: Iterable[smp_fs.RowNumberedItem],
    tool_inputs: dict[abc_tool_cfg.Names, abc_topic_res_items.Result],
    connector: abc_tool_visitor.ConnectorWithArguments,
) -> tuple[list[smp_fs.RowNumberedItem], list[smp_fs.RowNumberedItem]]:
    """Return row numbered samples to run and those with missing inputs."""
    checked_samples_to_run: list[smp_fs.RowNumberedItem] = []
    samples_with_missing_inputs: list[smp_fs.RowNumberedItem] = []

    for row_numbered_sample in samples_to_run:
        sample_missing_inputs = smp_miss_in.sample_list(
            tool_inputs,
            row_numbered_sample.item(),
            connector,
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
