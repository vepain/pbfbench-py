"""Experience monitors."""

from __future__ import annotations

import csv
from contextlib import contextmanager
from enum import StrEnum
from typing import TYPE_CHECKING, Literal, Self

import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.items as smp_items
import pbfbench.samples.status as smp_status

if TYPE_CHECKING:
    import _csv
    from collections.abc import Generator, Iterable, Iterator
    from pathlib import Path

    from . import file_system as exp_fs


class UnresolvedSamplesTSVHeader(StrEnum):
    """Unresolved samples TSV header."""

    ROW_NUMBER = "row_number"
    SPECIES_ID = "species_id"
    SAMPLE_ID = "sample_id"


class UnresolvedSamplesTSVReader:
    """Unresolved samples TSV reader."""

    HEADER = UnresolvedSamplesTSVHeader

    @classmethod
    @contextmanager
    def open(cls, file: Path) -> Generator[Self]:
        """Open TSV file for reading."""
        with file.open() as f_in:
            reader = cls(file, csv.reader(f_in, delimiter="\t"))
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

    def __iter__(self) -> Iterator[smp_fs.RowNumberedItem]:
        """Iterate over unresolved samples."""
        for row in self.__csv_reader:
            row_number = int(self.__get_cell(row, self.HEADER.ROW_NUMBER))
            species_id = self.__get_cell(row, self.HEADER.SPECIES_ID)
            sample_id = self.__get_cell(row, self.HEADER.SAMPLE_ID)
            yield smp_fs.RowNumberedItem(
                row_number,
                smp_items.Item(species_id, sample_id),
            )

    def __get_cell(self, row: list[str], column_id: UnresolvedSamplesTSVHeader) -> str:
        return row[self.__columns_index[column_id]]

    def __set_columns_index(self) -> dict[str, int]:
        """Set columns index."""
        header = next(self.__csv_reader)
        return {column_name: index for index, column_name in enumerate(header)}


# REFACTOR create abstract class for TSV readers and writers


class UnresolvedSamplesTSVWriter:
    """Unresolved samples TSV writer."""

    HEADER = UnresolvedSamplesTSVHeader

    @classmethod
    @contextmanager
    def auto_open(cls, file: Path) -> Generator[Self]:
        """Open TSV file for writing."""
        mode: Literal["w", "a"] = "a" if file.exists() else "w"
        with cls.open(file, mode) as writer:
            yield writer

    @classmethod
    @contextmanager
    def open(
        cls,
        file: Path,
        mode: Literal["w", "a"],
    ) -> Generator[Self]:
        """Open TSV file for writing."""
        match mode:
            case "w":
                columns_index = None
            case "a":
                if file.exists():
                    with UnresolvedSamplesTSVReader.open(file) as reader:
                        columns_index = reader.columns_index()
                else:
                    columns_index = None
        with file.open(mode) as f_out:
            writer = cls(
                file,
                csv.writer(f_out, delimiter="\t"),
                columns_index,
            )
            yield writer

    def __init__(
        self,
        file: Path,
        csv_writer: _csv._writer,
        columns_index: dict[str, int] | None,
    ) -> None:
        """Initialize object."""
        self.__file = file
        self.__csv_writer = csv_writer
        self.__columns_index = (
            columns_index if columns_index is not None else self.__write_header()
        )

    def file(self) -> Path:
        """Get TSV output file path."""
        return self.__file

    def columns_index(self) -> dict[str, int]:
        """Get columns index."""
        return self.__columns_index

    def write_unresolved_sample(
        self,
        unresolved_sample: smp_fs.RowNumberedItem,
    ) -> None:
        """Write error sample."""
        self.__csv_writer.writerow(
            [
                unresolved_sample.row_number(),
                unresolved_sample.item().species_id(),
                unresolved_sample.item().sample_id(),
            ],
        )

    def write_unresolved_samples(
        self,
        unresolved_samples: Iterable[smp_fs.RowNumberedItem],
    ) -> None:
        """Write unresolved samples."""
        for unresolved_sample in unresolved_samples:
            self.write_unresolved_sample(unresolved_sample)

    def __write_header(self) -> dict[str, int]:
        self.__csv_writer.writerow(map(str, self.HEADER))
        return {
            column_name: index
            for index, column_name in enumerate(map(str, self.HEADER))
        }


class ResolvedSample:
    """Resolved sample."""

    def __init__(
        self,
        exp_sample_id: str,
        status: smp_status.Status,
    ) -> None:
        """Initialize."""
        self.__exp_sample_id = exp_sample_id
        self.__status = status

    def exp_sample_id(self) -> str:
        """Get experiment sample ID."""
        return self.__exp_sample_id

    def status(self) -> smp_status.Status:
        """Get satus."""
        return self.__status


class ResolvedSamplesTSVHeader(StrEnum):
    """Resolved samples TSV header."""

    EXP_SAMPLE_ID = "exp_sample_id"
    STATUS = "status"


class ResolvedSampleTSVReader:
    """Error samples TSV reader."""

    HEADER = ResolvedSamplesTSVHeader

    @classmethod
    @contextmanager
    def open(cls, file: Path) -> Generator[Self]:
        """Open TSV file for reading."""
        with file.open() as f_in:
            reader = cls(file, csv.reader(f_in, delimiter="\t"))
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

    def __iter__(self) -> Iterator[ResolvedSample]:
        """Iterate over resolved samples."""
        for row in self.__csv_reader:
            exp_sample_id = self.__get_cell(row, self.HEADER.EXP_SAMPLE_ID)
            status = smp_status.status_from_str(
                self.__get_cell(row, self.HEADER.STATUS),
            )
            yield ResolvedSample(exp_sample_id, status)

    def __get_cell(self, row: list[str], column_id: ResolvedSamplesTSVHeader) -> str:
        return row[self.__columns_index[column_id]]

    def __set_columns_index(self) -> dict[str, int]:
        """Set columns index."""
        header = next(self.__csv_reader)
        return {column_name: index for index, column_name in enumerate(header)}


class ResolvedSamplesTSVWriter:
    """Resolved samples TSV writer."""

    HEADER = ResolvedSamplesTSVHeader

    @classmethod
    @contextmanager
    def auto_open(cls, file: Path) -> Generator[Self]:
        """Open TSV file for writing."""
        mode: Literal["w", "a"] = "a" if file.exists() else "w"
        with cls.open(file, mode) as writer:
            yield writer

    @classmethod
    @contextmanager
    def open(
        cls,
        file: Path,
        mode: Literal["w", "a"],
    ) -> Generator[Self]:
        """Open TSV file for writing."""
        match mode:
            case "w":
                columns_index = None
            case "a":
                if file.exists():
                    with UnresolvedSamplesTSVReader.open(file) as reader:
                        columns_index = reader.columns_index()
                else:
                    columns_index = None
        with file.open(mode) as f_out:
            writer = cls(
                file,
                csv.writer(f_out, delimiter="\t"),
                columns_index,
            )
            yield writer

    def __init__(
        self,
        file: Path,
        csv_writer: _csv._writer,
        columns_index: dict[str, int] | None,
    ) -> None:
        """Initialize object."""
        self.__file = file
        self.__csv_writer = csv_writer
        self.__columns_index = (
            columns_index if columns_index is not None else self.__write_header()
        )

    def file(self) -> Path:
        """Get TSV output file path."""
        return self.__file

    def columns_index(self) -> dict[str, int]:
        """Get columns index."""
        return self.__columns_index

    def write_resolved_sample(self, resolved_sample: ResolvedSample) -> None:
        """Write error sample."""
        self.__csv_writer.writerow(
            [
                resolved_sample.exp_sample_id(),
                resolved_sample.status(),
            ],
        )

    def write_resolved_samples(
        self,
        resolved_samples: Iterable[ResolvedSample],
    ) -> None:
        """Write error samples."""
        for resolved_sample in resolved_samples:
            self.write_resolved_sample(resolved_sample)

    def __write_header(self) -> dict[str, int]:
        self.__csv_writer.writerow(map(str, self.HEADER))
        return {
            column_name: index
            for index, column_name in enumerate(map(str, self.HEADER))
        }


def write_unresolved_samples(
    work_fs_manager: exp_fs.WorkManager,
    samples: Iterable[smp_fs.RowNumberedItem],
) -> None:
    """Write unresolved samples."""
    with UnresolvedSamplesTSVWriter.auto_open(
        work_fs_manager.unresolved_samples_tsv(),
    ) as writer:
        writer.write_unresolved_samples(samples)


def write_resolved_samples(
    work_fs_manager: exp_fs.WorkManager,
    samples_with_status: Iterable[tuple[smp_fs.RowNumberedItem, smp_status.Status]],
) -> None:
    """Write resolved samples."""
    with ResolvedSamplesTSVWriter.auto_open(
        work_fs_manager.resolved_samples_tsv(),
    ) as writer:
        writer.write_resolved_samples(
            ResolvedSample(sample.item().exp_sample_id(), status)
            for sample, status in samples_with_status
        )


def update_samples_resolution_status(
    work_fs_manager: exp_fs.WorkManager,
    samples_with_status: Iterable[tuple[smp_fs.RowNumberedItem, smp_status.Status]],
) -> None:
    """Move resolved samples from unresolved file to resolved file."""
    samples_with_status = list(samples_with_status)
    write_resolved_samples(work_fs_manager, samples_with_status)

    with UnresolvedSamplesTSVReader.open(
        work_fs_manager.unresolved_samples_tsv(),
    ) as reader:
        resolved_sample_row_numbers = {
            sample.row_number() for sample, _ in samples_with_status
        }
        new_unresolved_samples = [
            sample
            for sample in reader
            if sample.row_number() not in resolved_sample_row_numbers
        ]

    with UnresolvedSamplesTSVWriter.open(
        work_fs_manager.unresolved_samples_tsv(),
        "w",
    ) as writer:
        writer.write_unresolved_samples(new_unresolved_samples)


def iter_unresolved_samples(
    work_fs_manager: exp_fs.WorkManager,
) -> Iterator[smp_fs.RowNumberedItem]:
    """Iterate over unresolved samples."""
    with UnresolvedSamplesTSVReader.open(
        work_fs_manager.unresolved_samples_tsv(),
    ) as reader:
        yield from reader


def iter_resolved_samples(
    work_fs_manager: exp_fs.WorkManager,
) -> Iterator[ResolvedSample]:
    """Iterate over resolved samples."""
    with ResolvedSampleTSVReader.open(
        work_fs_manager.resolved_samples_tsv(),
    ) as reader:
        yield from reader
