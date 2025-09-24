"""Experiment iter module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pbfbench.abc.topic.results as abc_topic_res
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.status as smp_status

from . import errors as exp_errors
from . import file_system as exp_fs

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


def samples_with_status(
    data_exp_fs_manager: exp_fs.DataManager,
) -> Iterator[tuple[smp_fs.RowNumberedItem, smp_status.Status]]:
    """Get samples with their status."""
    with smp_fs.TSVReader.open(data_exp_fs_manager.samples_tsv()) as smp_tsv_in:
        return (
            (
                row_numbered_sample,
                smp_status.get_status(
                    data_exp_fs_manager.sample_fs_manager(row_numbered_sample.item()),
                ),
            )
            for row_numbered_sample in smp_tsv_in.iter_row_numbered_items()
        )


def samples_to_format_result(
    formatted_result_builder: abc_topic_res.Formatted,
    all_samples: Iterable[smp_fs.RowNumberedItem],
) -> Iterator[smp_fs.RowNumberedItem]:
    """Get input samples to format result.

    They correspond to input samples for which the experiment is done
    but the result is not formatted for the current tool.
    """
    # TODO log that requires to run before init
    # TODO perhaps missing inputs for check should be good (I removed it...)
    # Just for logs (only for init app in that case, bc run app will after logs it)
    return (
        row_numbered_sample
        for row_numbered_sample in all_samples
        if formatted_result_builder.check(row_numbered_sample.item())
        != smp_status.OK.OK
    )


def samples_to_complete(
    data_exp_fs_manager: exp_fs.DataManager,
) -> Iterator[smp_fs.RowNumberedItem]:
    """Get samples to complete."""
    # FIXME potentially useless
    with exp_errors.ErrorsTSVReader.open(
        data_exp_fs_manager.errors_tsv(),
    ) as in_exp_errors:
        samples_id_with_errors = {
            sample_error.exp_sample_id() for sample_error in in_exp_errors
        }
    return (
        row_numbered_item
        for row_numbered_item in samples_to_run(data_exp_fs_manager)
        if row_numbered_item.item().exp_sample_id() not in samples_id_with_errors
    )
