"""Tool connector module.

Make the connexion between:
1. argument (YAML) -> input (to check)
2. input (checked) -> shell lines builder
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import get_args

import pbfbench.abc.tool.config as abc_tool_config
import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.abc.tool.inputs as abc_tool_inputs
import pbfbench.abc.tool.shell as abc_tool_shell
import pbfbench.abc.topic.results.items as abc_topic_results
import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.experiment.file_system as exp_fs


class ArgumentPath[
    N: abc_tool_config.Names,
    T: abc_topic_visitor.Tools,
    R: abc_topic_results.Result,
    S: abc_tool_shell.ArgBashLinesBuilder,
]:
    """Tool connector."""

    def __init__(
        self,
        arg_name: N,
        topic_tools: type[T],
        fn_result_visitor: Callable[[T], type[R]],
        sh_lines_builder_type: type[S],
    ) -> None:
        """Initialize."""
        self.__arg_name = arg_name
        self.__topic_tools = topic_tools
        self.__fn_result_visitor = fn_result_visitor
        self.__sh_lines_builder_type = sh_lines_builder_type

    def arg_name(self) -> N:
        """Get argument name."""
        return self.__arg_name

    def topic_tools(self) -> type[T]:
        """Get topic tools."""
        return self.__topic_tools

    def fn_result_visitor(
        self,
    ) -> Callable[[T], type[R]]:
        """Get result visitor function."""
        return self.__fn_result_visitor

    def sh_lines_builder_type(self) -> type[S]:
        """Get shell lines builder type."""
        return self.__sh_lines_builder_type

    def arg_to_checkable_input(
        self,
        arguments: abc_tool_config.Arguments,
        data_dir: Path,
    ) -> R:
        """Convert argument to input."""
        arg = arguments[self.__arg_name]
        tool = self.__topic_tools(arg.tool_name())
        return self.fn_result_visitor()(tool)(
            exp_fs.Manager(data_dir, tool.to_description(), arg.exp_name()),
        )

    def input_to_sh_lines_builder(self, checked_input: R) -> S:
        """Convert input to shell lines builder."""
        return self.sh_lines_builder_type()(checked_input)


class Connector[
    Config: abc_tool_config.Config,
    Inputs: abc_tool_inputs.Inputs,
    Commands: abc_tool_shell.Commands,
](ABC):
    """Tool connectors."""

    @classmethod
    def config_type(cls) -> type[Config]:
        """Get config type."""
        return get_args(cls)[0]

    @classmethod
    def inputs_type(cls) -> type[Inputs]:
        """Get inputs type."""
        return get_args(cls)[1]

    @classmethod
    def commands_type(cls) -> type[Commands]:
        """Get commands type."""
        return get_args(cls)[2]

    @classmethod
    @abstractmethod
    def config_to_inputs(cls, config: Config, data_dir: Path) -> Inputs:
        """Convert config to inputs."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def inputs_to_commands(
        cls,
        config: Config,
        inputs: Inputs,
        working_exp_fs_manager: exp_fs.Manager,
    ) -> Commands:
        """Convert inputs to commands."""
        raise NotImplementedError

    def __init__(self, tool_description: abc_tool_desc.Description) -> None:
        """Initialize."""
        self.__tool_description = tool_description

    def tool_description(self) -> abc_tool_desc.Description:
        """Get tool description."""
        return self.__tool_description
