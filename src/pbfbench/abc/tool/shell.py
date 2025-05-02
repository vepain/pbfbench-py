"""Tools script logics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pbfbench.abc.tool.config as tool_cfg
import pbfbench.abc.topic.results.items as abc_topic_results
import pbfbench.experiment.file_system as exp_fs

if TYPE_CHECKING:
    from collections.abc import Iterator


class ArgBashLinesBuilder[R: abc_topic_results.Result](ABC):
    """Argument bash lines builder."""

    def __init__(self, tool_data_result: R) -> None:
        """Initialize."""
        self._tool_data_result = tool_data_result

    def tool_data_result(self) -> R:
        """Get tool data result."""
        return self._tool_data_result

    @abstractmethod
    def init_lines(self) -> Iterator[str]:
        """Get shell input init lines."""
        raise NotImplementedError

    @abstractmethod
    def argument(self) -> str:
        """Get shell input param lines."""
        raise NotImplementedError

    @abstractmethod
    def close_lines(self) -> Iterator[str]:
        """Get shell input close lines."""
        raise NotImplementedError


class Commands[N: tool_cfg.Names, O: tool_cfg.Options](ABC):
    """Tool command."""

    def __init__(
        self,
        arg_names_with_checked_inputs: dict[N, ArgBashLinesBuilder],
        options: O,
        working_exp_fs_manager: exp_fs.Manager,
    ) -> None:
        """Initialize."""
        self._arg_names_with_sh_lines_builders = arg_names_with_checked_inputs
        self._options = options
        self._working_exp_fs_manager = working_exp_fs_manager

    def options(self) -> O:
        """Get options."""
        return self._options

    def working_exp_fs_manager(self) -> exp_fs.Manager:
        """Get working experiment file system manager."""
        return self._working_exp_fs_manager

    def commands(self) -> Iterator[str]:
        """Iterate over the tool commands."""
        for result_lines_builder in self._arg_names_with_sh_lines_builders.values():
            yield from result_lines_builder.init_lines()
        yield ("")
        yield from self.core_commands()
        yield ("")
        for result_lines_builder in self._arg_names_with_sh_lines_builders.values():
            yield from result_lines_builder.close_lines()

    @abstractmethod
    def core_commands(self) -> Iterator[str]:
        """Iterate over the tool command lines."""
        raise NotImplementedError

    def lines_builder(self, name: N) -> ArgBashLinesBuilder:
        """Get result."""
        return self._arg_names_with_sh_lines_builders[name]

    def argument(self, name: N) -> str:
        """Get result."""
        return self.lines_builder(name).argument()
