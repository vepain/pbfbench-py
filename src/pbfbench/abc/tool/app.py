"""Tool abstract application module."""

# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.experiment.run as exp_run
from pbfbench import root_logging

_LOGGER = logging.getLogger(__name__)


class InitCommand:
    """Init command."""

    NAME = "init"
    HELP = "Initialize the tool experiment (format, etc.)"


class RunCommand:
    """Run command."""

    NAME = "run"
    HELP = "Run the tool experiment"


class CheckCommand:
    """Check command."""

    NAME = "check"
    HELP = "Check the tool experiment"


def build_application[Connector: abc_tool_visitor.Connector](
    run_app: RunApp[Connector],
) -> typer.Typer:
    """Build topic application."""
    tool_description = run_app.connector().tool_description()
    app = typer.Typer(
        name=tool_description.cmd(),
        help=f"Subcommand for tool `{tool_description.name()}`",
        rich_markup_mode="rich",
    )
    app.command(name=RunCommand.NAME, help=RunCommand.HELP)(run_app.run)
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


class RunApp[Connector: abc_tool_visitor.Connector]:
    """Run application."""

    def __init__(self, connector: Connector) -> None:
        """Initialize."""
        self.__connector = connector

    def connector(self) -> Connector:
        """Get connector."""
        return self.__connector

    def run(
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
                    result.number_of_samples_to_run(),
                    result.number_of_samples_to_run()
                    - len(result.samples_with_errors()),
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
            case exp_run.ErrorStatus.DIFFERENT_EXPERIMENT:
                _LOGGER.critical(
                    "The experiment in the data directory"
                    " does not have the same configuration of the current experiment.",
                )
