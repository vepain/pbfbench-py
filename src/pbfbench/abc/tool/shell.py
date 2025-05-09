"""Tools script logics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

import pbfbench.abc.module_meta as abc_meta_mod
import pbfbench.abc.tool.config as abc_tool_cfg
import pbfbench.abc.topic.results.items as abc_topic_res_items
import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.shell as smp_sh
import pbfbench.shell as sh

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path


class ArgBashLinesBuilder[R: abc_topic_res_items.Result](ABC):
    """Argument bash lines builder."""

    @classmethod
    def from_work_fs_manager(
        cls,
        input_result: R,
        work_exp_fs_manager: exp_fs.Manager,
    ) -> Self:
        """Create from work file system manager."""
        return cls(
            input_result,
            smp_sh.sample_shell_fs_manager(work_exp_fs_manager),
        )

    def __init__(
        self,
        input_result: R,
        working_smp_sh_fs_manager: smp_sh.smp_fs.Manager,
    ) -> None:
        """Initialize."""
        self._input_result = input_result
        self._input_data_smp_sh_fs_manager = smp_sh.sample_shell_fs_manager(
            input_result.exp_fs_manager(),
        )
        self._working_smp_sh_fs_manager = working_smp_sh_fs_manager

    def input_result(self) -> R:
        """Get input result."""
        return self._input_result

    def input_data_smp_sh_fs_manager(self) -> smp_sh.smp_fs.Manager:
        """Get input data sample shell file system manager."""
        return self._input_data_smp_sh_fs_manager

    def working_smp_sh_fs_manager(self) -> smp_sh.smp_fs.Manager:
        """Get working sample shell file system manager."""
        return self._working_smp_sh_fs_manager

    @abstractmethod
    def init_lines(self) -> Iterator[str]:
        """Get shell input init lines."""
        raise NotImplementedError

    @abstractmethod
    def close_lines(self) -> Iterator[str]:
        """Get shell input close lines."""
        raise NotImplementedError


class OptionBashLinesBuilder:
    """Bash lines builder for user tool options."""

    USER_TOOL_OPTIONS_VAR = sh.Variable("USER_TOOL_OPTIONS")

    def __init__(self, tool_options: abc_tool_cfg.StringOpts) -> None:
        """Initialize."""
        self.__tool_options = tool_options

    def tool_options(self) -> abc_tool_cfg.StringOpts:
        """Get tool options."""
        return self.__tool_options

    def set_options(self) -> Iterator[str]:
        """Set user tool options sh variable."""
        yield self.USER_TOOL_OPTIONS_VAR.set(
            "(" + " ".join(self.__tool_options) + ")",
        )


class Commands:
    """Tool command."""

    WORK_EXP_SAMPLE_DIR_VAR = sh.Variable("WORK_EXP_SAMPLE_DIR")

    CORE_COMMAND_SH_FILENAME = "core_command.sh"

    def __init__(
        self,
        arg_sh_lines_builders: Iterable[ArgBashLinesBuilder],
        opts_sh_lines_builder: OptionBashLinesBuilder,
        work_exp_fs_manager: exp_fs.Manager,
    ) -> None:
        """Initialize."""
        self._arg_sh_lines_builders = list(arg_sh_lines_builders)
        self._opts_sh_lines_builder = opts_sh_lines_builder
        self._work_exp_fs_manager = work_exp_fs_manager

    def arg_sh_lines_builders(self) -> Iterator[ArgBashLinesBuilder]:
        """Get argument bash lines builders."""
        yield from self._arg_sh_lines_builders

    def opts_sh_lines_builder(self) -> OptionBashLinesBuilder:
        """Get options bash lines builder."""
        return self._opts_sh_lines_builder

    def work_exp_fs_manager(self) -> exp_fs.Manager:
        """Get working experiment file system manager."""
        return self._work_exp_fs_manager

    def commands(self) -> Iterator[str]:
        """Iterate over the tool commands."""
        for result_lines_builder in self._arg_sh_lines_builders:
            yield from result_lines_builder.init_lines()
        yield ("")
        yield from self._opts_sh_lines_builder.set_options()
        yield ("")
        yield from self.core_commands()
        yield ("")
        for result_lines_builder in self._arg_sh_lines_builders:
            yield from result_lines_builder.close_lines()

    def set_work_sample_exp_dir(self) -> Iterator[str]:
        """Set working experiment sample directory."""
        work_exp_sample_dir = smp_sh.sample_shell_fs_manager(
            self._work_exp_fs_manager,
        ).sample_dir()
        yield self.WORK_EXP_SAMPLE_DIR_VAR.set(sh.path_to_str(work_exp_sample_dir))

    def core_commands(self) -> Iterator[str]:
        """Iterate over the tool command lines."""
        core_command_shell_path = self._core_command_shell_path()
        with core_command_shell_path.open("r") as in_core_cmd:
            for line in in_core_cmd:
                yield line.rstrip()

    def _core_command_shell_path(self) -> Path:
        """Get result."""
        return (
            abc_meta_mod.tool_module_path_from_descriptions(
                self._work_exp_fs_manager.tool_description().topic(),
                self._work_exp_fs_manager.tool_description(),
            )
            / self.CORE_COMMAND_SH_FILENAME
        )
