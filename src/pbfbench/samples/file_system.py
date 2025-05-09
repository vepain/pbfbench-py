"""Sample input-output module."""

from __future__ import annotations

import csv
from contextlib import contextmanager
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

import pbfbench.samples.items as smp_items

if TYPE_CHECKING:
    import _csv
    from collections.abc import Generator, Iterator


class Manager:
    """Sample file system manager."""

    SBATCH_STATS_PSV_NAME = Path("sbatch_stats.psv")

    MISSING_INPUTS_TSV_NAME = Path("missing_inputs.tsv")
    ERRORS_LOG_NAME = Path("errors.log")
    DONE_LOG_NAME = Path("done.log")

    def __init__(self, sample_dir: Path) -> None:
        """Inititialize."""
        self.__sample_dir = sample_dir

    def sample_dir(self) -> Path:
        """Get sample directory path."""
        return self.__sample_dir

    def sbatch_stats_psv(self) -> Path:
        """Get sbatch stats file path."""
        return self.__sample_dir / self.SBATCH_STATS_PSV_NAME

    def missing_inputs_tsv(self) -> Path:
        """Get missing_inputs file path."""
        return self.__sample_dir / self.MISSING_INPUTS_TSV_NAME

    def errors_log(self) -> Path:
        """Get errors file."""
        return self.__sample_dir / self.ERRORS_LOG_NAME

    def done_log(self) -> Path:
        """Get done file."""
        return self.__sample_dir / self.DONE_LOG_NAME


def clean_error_logs(sample_fs_manager: Manager) -> None:
    """Clean experiment logs."""
    sample_fs_manager.missing_inputs_tsv().unlink(missing_ok=True)
    sample_fs_manager.errors_log().unlink(missing_ok=True)


class TSVHeader(StrEnum):
    """TSV header."""

    SPECIES_ID = "species_id"
    SAMPLE_ID = "sample_id"


class TSVReader:
    """Samples TSV reader."""

    @classmethod
    @contextmanager
    def open(cls, file: Path) -> Generator[TSVReader]:
        """Open TSV file for reading."""
        with file.open() as f_in:
            reader = TSVReader(file, csv.reader(f_in, delimiter="\t"))
            yield reader

    def __init__(self, file: Path, csv_reader: _csv._reader) -> None:
        """Initialize object."""
        self.__file = file
        self.__csv_reader = csv_reader
        self.__columns_index = self.__set_columns_index()

    def file(self) -> Path:
        """Get file."""
        return self.__file

    def columns_index(self) -> dict[str, int]:
        """Get columns index."""
        return self.__columns_index

    def iter_row_numbered_items(self) -> Iterator[RowNumberedItem]:
        """Iterate over row numbered items."""
        return (
            RowNumberedItem(row_number, sample_item)
            for row_number, sample_item in enumerate(self)
        )

    def __iter__(self) -> Iterator[smp_items.Item]:
        """Iterate sequence probability scores."""
        return (
            smp_items.Item(
                row[self.__columns_index[TSVHeader.SPECIES_ID]],
                row[self.__columns_index[TSVHeader.SAMPLE_ID]],
            )
            for row in self.__csv_reader
        )

    def __set_columns_index(self) -> dict[str, int]:
        """Set columns index."""
        header = next(self.__csv_reader)
        return {column_name: index for index, column_name in enumerate(header)}


def columns_name_index(file: Path) -> dict[str, int]:
    """Get columns name index."""
    with TSVReader.open(file) as reader:
        return reader.columns_index()


class RowNumberedItem:
    """Row numbered sample item."""

    def __init__(self, number: int, item: smp_items.Item) -> None:
        """Initialize."""
        self.__number = number
        self.__item = item

    def row_number(self) -> int:
        """Get row number."""
        return self.__number

    def item(self) -> smp_items.Item:
        """Get item."""
        return self.__item


def to_line_number_base_one(row_numbered_item: RowNumberedItem) -> int:
    """Get line number with a base 1.

    The header is at line number 1 (base 1).
    So the first item row (base 0, row number is 0)
    is associated to line number 2 (base 1).
    """
    return row_numbered_item.row_number() + 2
