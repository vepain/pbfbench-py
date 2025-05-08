"""Tool abstract application module."""

# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

import pbfbench.abc.app as abc_app
import pbfbench.abc.tool.config as abc_tool_config
import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.experiment.config as exp_cfg
import pbfbench.experiment.run as exp_run
import pbfbench.slurm.config as slurm_cfg
from pbfbench import root_logging

_LOGGER = logging.getLogger(__name__)


def build_application[ArgNames: abc_tool_config.Names](
    connector: abc_tool_visitor.Connector[ArgNames],
) -> typer.Typer:
    """Build topic application."""
    tool_description = connector.description()
    app = typer.Typer(
        name=tool_description.cmd(),
        help=f"Subcommand for tool `{tool_description.name()}`",
        rich_markup_mode="rich",
    )
    run_app = RunApp(connector)
    app.command(name=run_app.NAME, help=run_app.help())(run_app.main)
    config_app = ConfigApp(connector)
    app.command(name=config_app.NAME, help=config_app.help())(config_app.main)
    # TODO add check when ready
    return app


class Arguments:
    """Tool aaplication arguments."""

    DATA_DIR = typer.Argument(
        help="Path to the data directory (preferably absolute)",
    )
    WORK_DIR = typer.Argument(
        help="Path to the working directory (preferably absolute)",
    )
    EXP_CONFIG_YAML = typer.Argument(
        help="Path to the experiment configuration YAML file (preferably absolute)",
    )


class RunApp[ArgNames: abc_tool_config.Names]:
    """Run application."""

    NAME = abc_app.FinalCommands.RUN

    def __init__(self, connector: abc_tool_visitor.Connector[ArgNames]) -> None:
        """Initialize."""
        self.__connector = connector

    def connector(self) -> abc_tool_visitor.Connector[ArgNames]:
        """Get connector."""
        return self.__connector

    def help(self) -> str:
        """Get help string."""
        return f"Run {self.__connector.description().name()} tool."

    def main(
        self,
        data_dir: Annotated[Path, Arguments.DATA_DIR],
        work_dir: Annotated[Path, Arguments.WORK_DIR],
        exp_config_yaml: Annotated[Path, Arguments.EXP_CONFIG_YAML],
        debug: Annotated[bool, root_logging.OPT_DEBUG] = False,
    ) -> None:
        """Run tool."""
        root_logging.init_logger(_LOGGER, "Run tool", debug)
        #
        # Resolve absolute paths
        #
        data_dir = data_dir.resolve()
        work_dir = work_dir.resolve()
        exp_config_yaml = exp_config_yaml.resolve()
        #
        # Use the tool connector to run the experiment
        #
        match result := exp_run.run_experiment_on_samples(
            data_dir,
            work_dir,
            exp_config_yaml,
            self.__connector,
        ):
            case exp_run.RunStats():
                _number_of_running_samples = result.number_of_samples_to_run() - len(
                    result.samples_with_missing_inputs(),
                )
                _LOGGER.info(
                    "Total number of samples: %d\n"
                    "* Number of already done samples: %d\n"
                    "* Samples with missing inputs: %d\n"
                    "* Number of running samples: %d\n"
                    "  * Number of successfully run samples: %d\n"
                    "  * Number of samples which exit with errors: %d\n",
                    result.number_of_samples(),
                    result.number_of_samples() - result.number_of_samples_to_run(),
                    len(result.samples_with_missing_inputs()),
                    _number_of_running_samples,
                    _number_of_running_samples - len(result.samples_with_errors()),
                    len(result.samples_with_errors()),
                )
                typer.Exit(0)
            case exp_run.ErrorStatus.NO_WRITE_ACCESS:
                _LOGGER.info("Please check you have the write access.")
                typer.Exit(1)
            case exp_run.ErrorStatus.NO_READ_ACCESS:
                _LOGGER.info("Please check you have the read access.")
                typer.Exit(1)
            case exp_run.ErrorStatus.NO_TOOL_ENV_WRAPPER_SCRIPT:
                _LOGGER.critical(
                    "The experiment in the data directory"
                    " does not have the tool environment wrapper script.",
                )
                typer.Exit(1)
            case exp_run.ErrorStatus.WRONG_EXPERIMENT_CONFIG_SYNTAX:
                _LOGGER.critical(
                    "The experiment configuration file has a wrong syntax.",
                )
                typer.Exit(1)
            case exp_run.ErrorStatus.WRONG_ARGUMENTS:
                _LOGGER.critical(
                    "The experiment configuration file has wrong arguments.",
                )
                typer.Exit(1)
            case exp_run.ErrorStatus.DIFFERENT_EXPERIMENT:
                _LOGGER.critical(
                    "The experiment in the data directory"
                    " does not have the same configuration of the current experiment.",
                )


class ConfigApp[ArgsNames: abc_tool_config.Names]:
    """Run application."""

    NAME = "config"

    def __init__(self, connector: abc_tool_visitor.Connector[ArgsNames]) -> None:
        """Initialize."""
        self.__connector = connector

    def connector(self) -> abc_tool_visitor.Connector[ArgsNames]:
        """Get connector."""
        return self.__connector

    def help(self) -> str:
        """Get help string."""
        return (
            "Get draft "
            + self.__connector.description().name()
            + " tool configuration."
        )

    def main(
        self,
        config_exp_yaml: Annotated[Path, Arguments.EXP_CONFIG_YAML],
        debug: Annotated[bool, root_logging.OPT_DEBUG] = False,
    ) -> None:
        """Get draft config."""
        root_logging.init_logger(_LOGGER, "Tool config helper", debug)
        _cfg_type: type[exp_cfg.Config] = self.__connector.config_type()
        _tool_cfg_type: type[abc_tool_config.Config] = _cfg_type.tool_cfg_type()
        _tool_args_type: type[abc_tool_config.Arguments] = (
            _tool_cfg_type.arguments_type()
        )
        arguments = self._create_args(_tool_args_type)
        tool_opts = abc_tool_config.StringOpts(
            ("--options1=value1", "--options2=value2"),
        )

        tool_configs = _tool_cfg_type(arguments, tool_opts)
        slurm_config = slurm_cfg.Config(
            [
                "--mem=4096",
                "--cpus-per-task=4",
                "--time=1:00:00",
                "--account=my-account_name",
            ],
        )
        config = _cfg_type("$experiment_name", tool_configs, slurm_config)

        config.to_yaml(config_exp_yaml)
        _LOGGER.info("Tool configuration written to %s", config_exp_yaml)

    def _create_args(
        self,
        tool_args_type: type[abc_tool_config.Arguments],
    ) -> abc_tool_config.Arguments:
        """Create arguments."""
        args: dict[abc_tool_config.Names, abc_tool_config.Arg] = {}
        for arg_name, arg_path in self.__connector.arg_names_and_paths():
            topic_tools: type[abc_topic_visitor.Tools] = arg_path.topic_tools()
            tool_choices = [
                tool.to_description().name()
                for tool in topic_tools
                if arg_path.check_tool_implement_result(tool)
            ]
            tool_choice_str = " | ".join(tool_choices)
            args[arg_name] = abc_tool_config.Arg(
                tool_choice_str,
                "$input_experiment_name",
            )
        return tool_args_type(args)
