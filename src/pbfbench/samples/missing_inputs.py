"""Sample missing inputs."""

from __future__ import annotations

import csv
import logging
from contextlib import contextmanager
from enum import StrEnum
from typing import TYPE_CHECKING

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.abc.topic.results.items as abc_topic_results
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.status as smp_status
import pbfbench.topics.items as topics_items
import pbfbench.topics.visitor as topics_visitor

if TYPE_CHECKING:
    import _csv
    from collections.abc import Generator, Iterable, Iterator
    from pathlib import Path

_LOGGER = logging.getLogger(__name__)


class MissingInput:
    """Missing input item."""

    @classmethod
    def from_tool_input(
        cls,
        arg_name: str,
        tool_input: abc_topic_results.Result,
        reason: smp_status.ErrorStatus,
    ) -> MissingInput:
        """Create missing input from tool input."""
        return cls(
            str(arg_name),
            tool_input.exp_fs_manager().tool_description(),
            tool_input.exp_fs_manager().experiment_name(),
            reason,
            tool_input.origin_cmd(),
        )

    def __init__(
        self,
        arg_name: str,
        tool_description: abc_tool_desc.Description,
        experiment_name: str,
        reason: smp_status.ErrorStatus,
        help_string: str,
    ) -> None:
        """Initialize."""
        self.__arg_name = arg_name
        self.__tool_desc = tool_description
        self.__exp_name = experiment_name
        self.__reason = reason
        self.__help_string = help_string

    def arg_name(self) -> str:
        """Get argument name."""
        return self.__arg_name

    def tool_description(self) -> abc_tool_desc.Description:
        """Get tool description."""
        return self.__tool_desc

    def experiment_name(self) -> str:
        """Get experiment name."""
        return self.__exp_name

    def reason(self) -> smp_status.ErrorStatus:
        """Get reason."""
        return self.__reason

    def help(self) -> str:
        """Get help string."""
        return self.__help_string


class MissingInputsTSVHeader(StrEnum):
    """Missing inputs TSV header."""

    ARG_NAME = "arg_name"
    TOPIC = "input_topic"
    TOOL = "input_tool"
    EXPERIMENT = "input_experiment"
    REASON = "reason"
    HELP = "help"


class MissingInputsTSVReader:
    """Missing inputs TSV reader."""

    @classmethod
    @contextmanager
    def open(cls, file: Path) -> Generator[MissingInputsTSVReader]:
        """Open TSV file for reading."""
        with file.open() as f_in:
            reader = MissingInputsTSVReader(file, csv.reader(f_in, delimiter="\t"))
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

    def __iter__(self) -> Iterator[MissingInput]:
        """Iterate over missing inputs items."""
        for row in self.__csv_reader:
            arg_name = self.__get_cell(row, MissingInputsTSVHeader.ARG_NAME)
            topic_name = topics_items.Names(
                self.__get_cell(row, MissingInputsTSVHeader.TOPIC),
            )
            tool_str = self.__get_cell(row, MissingInputsTSVHeader.TOOL)
            tool_name = topics_visitor.tools(topic_name)(tool_str)
            exp_name = self.__get_cell(row, MissingInputsTSVHeader.EXPERIMENT)
            help_string = self.__get_cell(row, MissingInputsTSVHeader.HELP)
            yield MissingInput(
                arg_name,
                tool_name.to_description(),
                exp_name,
                smp_status.ErrorStatus(
                    self.__get_cell(row, MissingInputsTSVHeader.REASON),
                ),
                help_string,
            )

    def __get_cell(self, row: list[str], column_id: MissingInputsTSVHeader) -> str:
        return row[self.__columns_index[column_id]]

    def __set_columns_index(self) -> dict[str, int]:
        """Set columns index."""
        header = next(self.__csv_reader)
        return {column_name: index for index, column_name in enumerate(header)}


class MissingInputsTSVWriter:
    """Missing inputs TSV writer."""

    @classmethod
    @contextmanager
    def open(cls, file: Path) -> Generator[MissingInputsTSVWriter]:
        """Open TSV file for writing."""
        with file.open("w") as f_out:
            reader = MissingInputsTSVWriter(file, csv.writer(f_out, delimiter="\t"))
            yield reader

    def __init__(self, file: Path, csv_writer: _csv._writer) -> None:
        """Initialize object."""
        self.__file = file
        self.__csv_writer = csv_writer
        self.__columns_index = self.__write_header()

    def file(self) -> Path:
        """Get TSV output file path."""
        return self.__file

    def columns_index(self) -> dict[str, int]:
        """Get columns index."""
        return self.__columns_index

    def write_missing_input(self, missing_input: MissingInput) -> None:
        """Write missing input."""
        self.__csv_writer.writerow(
            [
                missing_input.arg_name(),
                missing_input.tool_description().topic().name(),
                missing_input.tool_description().name(),
                missing_input.experiment_name(),
                missing_input.reason(),
                missing_input.help(),
            ],
        )

    def write_missing_inputs(self, missing_inputs: Iterable[MissingInput]) -> None:
        """Write missing inputs."""
        for missing_input in missing_inputs:
            self.write_missing_input(missing_input)

    def __write_header(self) -> dict[str, int]:
        header_names = [
            MissingInputsTSVHeader.ARG_NAME,
            MissingInputsTSVHeader.TOPIC,
            MissingInputsTSVHeader.TOOL,
            MissingInputsTSVHeader.EXPERIMENT,
            MissingInputsTSVHeader.REASON,
            MissingInputsTSVHeader.HELP,
        ]
        if len(header_names) != len(MissingInputsTSVHeader):
            _err_msg = (
                f"Header names do not match enum:"
                f" {len(header_names)} != {len(MissingInputsTSVHeader)}"
            )
            _LOGGER.error(_err_msg)
            raise ValueError(_err_msg)
        self.__csv_writer.writerow(header_names)
        return {column_name: index for index, column_name in enumerate(header_names)}


def write_sample_missing_inputs(
    sample_fs_manager: smp_fs.Manager,
    sample_missing_inputs: Iterable[MissingInput],
) -> None:
    """Write sample missing inputs."""
    with MissingInputsTSVWriter.open(
        sample_fs_manager.missing_inputs_tsv(),
    ) as out_miss_inputs:
        out_miss_inputs.write_missing_inputs(sample_missing_inputs)
