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
        self.__tool_data_result = tool_data_result

    def tool_data_result(self) -> R:
        """Get tool data result."""
        return self.__tool_data_result

    @abstractmethod
    def sh_init_lines(self) -> Iterator[str]:
        """Get shell input init lines."""
        raise NotImplementedError

    @abstractmethod
    def sh_param_lines(self) -> Iterator[str]:
        """Get shell input param lines."""
        raise NotImplementedError

    @abstractmethod
    def sh_close_lines(self) -> Iterator[str]:
        """Get shell input close lines."""
        raise NotImplementedError


class Commands[O: tool_cfg.Options](ABC):
    """Tool command."""

    def __init__(
        self,
        options: O,
        working_exp_fs_manager: exp_fs.Manager,
    ) -> None:
        self.__options = options
        self.__working_exp_fs_manager = working_exp_fs_manager

    def options(self) -> O:
        """Get options."""
        return self.__options

    def working_exp_fs_manager(self) -> exp_fs.Manager:
        """Get working experiment file system manager."""
        return self.__working_exp_fs_manager

    @abstractmethod
    def commands(self) -> Iterator[str]:
        """Iterate over the tool command lines."""
        raise NotImplementedError
