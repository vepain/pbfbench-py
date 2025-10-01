"""Experiment iter module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.status as smp_status

if TYPE_CHECKING:
    from collections.abc import Iterator

    from . import file_system as exp_fs


def samples_with_status(
    data_exp_fs_manager: exp_fs.DataManager,
) -> Iterator[tuple[smp_fs.RowNumberedItem, smp_status.Status]]:
    """Get samples with their status."""
    with smp_fs.TSVReader.open(data_exp_fs_manager.samples_tsv()) as smp_tsv_in:
        for row_numbered_sample in smp_tsv_in.iter_row_numbered_items():
            yield (
                row_numbered_sample,
                smp_status.get_status(
                    data_exp_fs_manager.sample_fs_manager(row_numbered_sample.item()),
                ),
            )
