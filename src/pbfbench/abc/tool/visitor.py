"""Tool connector module.

Make the connexion between:
1. argument (YAML) -> input (to check)
2. input (checked) -> shell lines builder
"""

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from pathlib import Path

import pbfbench.abc.tool.config as abc_tool_config
import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.abc.tool.shell as abc_tool_shell
import pbfbench.abc.topic.results.items as abc_topic_results
import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.experiment.config as exp_cfg
import pbfbench.experiment.file_system as exp_fs


class ArgumentPath[
    T: abc_topic_visitor.Tools,
    R: abc_topic_results.Result,
    S: abc_tool_shell.ArgBashLinesBuilder,
]:
    """Tool connector."""

    def __init__(
        self,
        topic_tools: type[T],
        fn_result_visitor: Callable[[T], type[R]],
        sh_lines_builder_type: type[S],
    ) -> None:
        """Initialize."""
        self._topic_tools = topic_tools
        self._fn_result_visitor = fn_result_visitor
        self._sh_lines_builder_type = sh_lines_builder_type

    def topic_tools(self) -> type[T]:
        """Get topic tools."""
        return self._topic_tools

    def fn_result_visitor(
        self,
    ) -> Callable[[T], type[R]]:
        """Get result visitor function."""
        return self._fn_result_visitor

    def sh_lines_builder_type(self) -> type[S]:
        """Get shell lines builder type."""
        return self._sh_lines_builder_type

    def arg_to_checkable_input(
        self,
        data_dir: Path,
        tool: T,
        exp_name: str,
    ) -> R:
        """Convert argument to input."""
        return self.fn_result_visitor()(tool)(
            exp_fs.Manager(data_dir, tool.to_description(), exp_name),
        )

    def input_to_sh_lines_builder(
        self,
        checked_input: R,
        working_exp_fs_manager: exp_fs.Manager,
    ) -> S:
        """Convert input to shell lines builder."""
        return self.sh_lines_builder_type()(checked_input, working_exp_fs_manager)


class Connector[
    ArgNames: abc_tool_config.Names,
    ExpConfig: exp_cfg.Config,
    Commands: abc_tool_shell.Commands,
](ABC):
    """Tool connectors."""

    @classmethod
    @abstractmethod
    def config_type(cls) -> type[ExpConfig]:
        """Get experiment config type."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def commands_type(cls) -> type[Commands]:
        """Get commands type."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def tool_description(cls) -> abc_tool_desc.Description:
        """Get tool description."""
        raise NotImplementedError

    @classmethod
    def read_config(cls, config_path: Path) -> ExpConfig:
        """Read config."""
        return cls.config_type().from_yaml(config_path)

    def __init__(
        self,
        arg_names_and_paths: dict[ArgNames, ArgumentPath],
    ) -> None:
        """Initialize."""
        self._arg_names_and_paths = dict(arg_names_and_paths)

    def arg_names_and_paths(self) -> Iterator[tuple[ArgNames, ArgumentPath]]:
        """Get argument names and paths."""
        yield from self._arg_names_and_paths.items()

    def config_to_inputs(
        self,
        config: ExpConfig,
        data_fs_manager: exp_fs.Manager,
    ) -> dict[abc_tool_config.Names, abc_topic_results.Result]:
        """Convert config to inputs."""
        tool_config: abc_tool_config.Config = config.tool_configs()
        arguments: abc_tool_config.Arguments = tool_config.arguments()
        return {
            name: arg_path.arg_to_checkable_input(
                data_fs_manager.root_dir(),
                name.topic_tools()(arguments[name].tool_name()),
                arguments[name].exp_name(),
            )
            for name, arg_path in self._arg_names_and_paths.items()
        }

    def inputs_to_commands(
        self,
        config: ExpConfig,
        arg_names_with_checked_inputs: dict[
            abc_tool_config.Names,
            abc_topic_results.Result,
        ],
        working_exp_fs_manager: exp_fs.Manager,
    ) -> Commands:
        """Convert inputs to commands."""
        tool_config: abc_tool_config.Config = config.tool_configs()
        options: abc_tool_config.Options = tool_config.options()
        return self.commands_type()(
            {
                name: arg_path.input_to_sh_lines_builder(
                    arg_names_with_checked_inputs[name],
                    working_exp_fs_manager,
                )
                for name, arg_path in self._arg_names_and_paths.items()
            },
            options,
            working_exp_fs_manager,
        )
