"""Tool connector module.

Make the connexion between:
1. argument (YAML) -> input (to check)
2. input (checked) -> shell lines builder
"""

from abc import abstractmethod
from collections.abc import Iterator
from pathlib import Path

import pbfbench.abc.tool.config as abc_tool_config
import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.abc.tool.shell as abc_tool_shell
import pbfbench.abc.topic.results.items as abc_topic_res_items
import pbfbench.abc.topic.results.visitors as topic_res_visitors
import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.experiment.config as exp_cfg
import pbfbench.experiment.file_system as exp_fs


class ArgumentPath[
    T: abc_topic_visitor.Tools,
    R: abc_topic_res_items.Result,
]:
    """Tool connector."""

    def __init__(
        self,
        topic_tools: type[T],
        result_visitor: type[topic_res_visitors.Visitor[T, R]],
        sh_lines_builder_type: type[abc_tool_shell.ArgBashLinesBuilder[R]],
    ) -> None:
        """Initialize."""
        self._topic_tools = topic_tools
        self._result_visitor = result_visitor
        self._sh_lines_builder_type = sh_lines_builder_type

    def topic_tools(self) -> type[T]:
        """Get topic tools."""
        return self._topic_tools

    def result_visitor(
        self,
    ) -> type[topic_res_visitors.Visitor[T, R]]:
        """Get result visitor function."""
        return self._result_visitor

    def sh_lines_builder_type(self) -> type[abc_tool_shell.ArgBashLinesBuilder[R]]:
        """Get shell lines builder type."""
        return self._sh_lines_builder_type

    def check_tool_implement_result(self, tool: T) -> bool:
        """Check tool implement result."""
        try:
            self._result_visitor.result_builder_from_tool(tool)
        except ValueError:
            return False
        return True

    def arg_to_checkable_input(
        self,
        data_fs_manager: exp_fs.Manager,
        arg: abc_tool_config.Arg,
    ) -> R:
        """Convert argument to input."""
        tool = self._topic_tools(arg.tool_name())
        exp_name = arg.exp_name()
        return self._result_visitor.result_builder_from_tool(tool)(
            exp_fs.Manager(data_fs_manager.root_dir(), tool.to_description(), exp_name),
        )

    def input_to_sh_lines_builder(
        self,
        data_fs_manager: exp_fs.Manager,
    ) -> abc_tool_shell.ArgBashLinesBuilder[R]:
        """Convert input to shell lines builder."""
        return self._sh_lines_builder_type.from_data_fs_manager(data_fs_manager)


class Connector[ArgNames: abc_tool_config.Names]:
    """Tool connectors."""

    @classmethod
    @abstractmethod
    def config_type(cls) -> type[exp_cfg.Config[ArgNames]]:
        """Get experiment config type."""
        raise NotImplementedError

    def __init__(
        self,
        tool_description: abc_tool_desc.Description,
        arg_names_and_paths: dict[ArgNames, ArgumentPath],
    ) -> None:
        """Initialize."""
        self._tool_description = tool_description
        self._arg_names_and_paths = dict(arg_names_and_paths)

    def description(self) -> abc_tool_desc.Description:
        """Get tool description."""
        return self._tool_description

    def arg_names_and_paths(self) -> Iterator[tuple[ArgNames, ArgumentPath]]:
        """Get argument names and paths."""
        yield from self._arg_names_and_paths.items()

    def read_config(self, config_path: Path) -> exp_cfg.Config[ArgNames]:
        """Read config."""
        return self.config_type().from_yaml(config_path)

    def check_arguments_implement_results(
        self,
        config: exp_cfg.Config[ArgNames],
    ) -> list[ValueError]:
        """Check arguments implement results."""
        value_errors: list[ValueError] = []
        tool_config: abc_tool_config.Config = config.tool_configs()
        arguments: abc_tool_config.Arguments = tool_config.arguments()
        for name, arg_path in self._arg_names_and_paths.items():
            ok_tool_set_str: str = (
                "{"
                + ", ".join(
                    [
                        str(tool)
                        for tool in arg_path.topic_tools()
                        if arg_path.check_tool_implement_result(tool)
                    ],
                )
                + "}"
            )
            try:
                tool = name.topic_tools()(arguments[name].tool_name())
            except ValueError:
                _err_msg = (
                    f"For argument `{name}`: "
                    f"`{arguments[name].tool_name()}` is none of the tools"
                    f" in {ok_tool_set_str}"
                )
                value_errors.append(ValueError(_err_msg))
            else:
                try:
                    arg_path.result_visitor().result_builder_from_tool(tool)
                except ValueError as value_error:
                    _err_msg = (
                        f"For argument `{name}`: "
                        f"{value_error}"
                        f" (choose one of the tool in {ok_tool_set_str})"
                    )
                    value_errors.append(ValueError(_err_msg))
        return value_errors

    def config_to_inputs(
        self,
        config: exp_cfg.Config[ArgNames],
        data_fs_manager: exp_fs.Manager,
    ) -> dict[abc_tool_config.Names, abc_topic_res_items.Result]:
        """Convert config to inputs."""
        tool_config: abc_tool_config.Config = config.tool_configs()
        arguments: abc_tool_config.Arguments = tool_config.arguments()
        names_with_results: dict[
            abc_tool_config.Names,
            abc_topic_res_items.Result,
        ] = {}
        for name, arg_path in self._arg_names_and_paths.items():
            result: abc_topic_res_items.Result = arg_path.arg_to_checkable_input(
                data_fs_manager,
                arguments[name],
            )
            names_with_results[name] = result
        return names_with_results

    def inputs_to_commands(
        self,
        config: exp_cfg.Config[ArgNames],
        data_fs_manager: exp_fs.Manager,
        working_exp_fs_manager: exp_fs.Manager,
    ) -> abc_tool_shell.Commands:
        """Convert inputs to commands."""
        tool_config: abc_tool_config.Config = config.tool_configs()
        return abc_tool_shell.Commands(
            [
                arg_path.input_to_sh_lines_builder(data_fs_manager)
                for arg_path in self._arg_names_and_paths.values()
            ],
            abc_tool_shell.OptionBashLinesBuilder(tool_config.options()),
            working_exp_fs_manager,
        )
