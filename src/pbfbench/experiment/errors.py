"""Experiment errors module."""

from __future__ import annotations

import csv
import logging
from contextlib import contextmanager
from enum import StrEnum
from typing import TYPE_CHECKING, Literal

import pbfbench.samples.status as smp_status

if TYPE_CHECKING:
    import _csv
    from collections.abc import Generator, Iterable, Iterator
    from pathlib import Path

_LOGGER = logging.getLogger(__name__)


class SampleError:
    """Sample error."""

    def __init__(
        self,
        sample_id: str,
        reason: smp_status.ErrorStatus,
    ) -> None:
        """Initialize."""
        self.__sample_id = sample_id
        self.__reason = reason

    def sample_id(self) -> str:
        """Get sample ID."""
        return self.__sample_id

    def reason(self) -> smp_status.ErrorStatus:
        """Get reason."""
        return self.__reason


class ErrorsTSVHeader(StrEnum):
    """Error samples TSV header."""

    SAMPLE_ID = "sample_id"
    REASON = "reason"


class ErrorsTSVReader:
    """Error samples TSV reader."""

    @classmethod
    @contextmanager
    def open(cls, file: Path) -> Generator[ErrorsTSVReader]:
        """Open TSV file for reading."""
        with file.open() as f_in:
            reader = ErrorsTSVReader(file, csv.reader(f_in, delimiter="\t"))
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

    def __iter__(self) -> Iterator[SampleError]:
        """Iterate over error samples."""
        for row in self.__csv_reader:
            sample_id = self.__get_cell(row, ErrorsTSVHeader.SAMPLE_ID)
            error_status = smp_status.ErrorStatus(
                self.__get_cell(row, ErrorsTSVHeader.REASON),
            )
            yield SampleError(sample_id, error_status)

    def __get_cell(self, row: list[str], column_id: ErrorsTSVHeader) -> str:
        return row[self.__columns_index[column_id]]

    def __set_columns_index(self) -> dict[str, int]:
        """Set columns index."""
        header = next(self.__csv_reader)
        return {column_name: index for index, column_name in enumerate(header)}


class ErrorsTSVWriter:
    """Error samples TSV writer."""

    @classmethod
    @contextmanager
    def open(cls, file: Path, mode: Literal["w", "a"]) -> Generator[ErrorsTSVWriter]:
        """Open TSV file for writing."""
        match mode:
            case "w":
                columns_index = None
            case "a":
                with ErrorsTSVReader.open(file) as reader:
                    columns_index = reader.columns_index()
        with file.open(mode) as f_out:
            writer = ErrorsTSVWriter(
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

    def write_error_sample(self, error_sample: SampleError) -> None:
        """Write error sample."""
        self.__csv_writer.writerow(
            [
                error_sample.sample_id(),
                error_sample.reason(),
            ],
        )

    def write_error_samples(self, error_samples: Iterable[SampleError]) -> None:
        """Write error samples."""
        for error_sample in error_samples:
            self.write_error_sample(error_sample)

    def __write_header(self) -> dict[str, int]:
        header_names = [ErrorsTSVHeader.SAMPLE_ID, ErrorsTSVHeader.REASON]
        if len(header_names) != len(ErrorsTSVHeader):
            _err_msg = (
                f"Header names do not match enum:"
                f" {len(header_names)} != {len(ErrorsTSVHeader)}"
            )
            _LOGGER.error(_err_msg)
            raise ValueError(_err_msg)
        self.__csv_writer.writerow(header_names)
        return {column_name: index for index, column_name in enumerate(header_names)}
