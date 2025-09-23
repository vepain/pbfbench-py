"""Tool abstract application module."""

# Due to typer usage:
# ruff: noqa: TC003, FBT002, FBT001

from __future__ import annotations

import datetime
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, TypeVar, final

import typer

import pbfbench.abc.app as abc_app
import pbfbench.experiment.checks as exp_checks
import pbfbench.experiment.complete as exp_complete
import pbfbench.experiment.file_system as exp_fs
import pbfbench.experiment.managers as exp_managers
import pbfbench.experiment.run as exp_run
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.status as smp_status
import pbfbench.slurm.config as slurm_cfg
from pbfbench import root_logging

from . import config as abc_tool_cfg
from . import connector as abc_tool_connector

_LOGGER = logging.getLogger(__name__)


def log_filename() -> Path:
    """Get log filename."""
    return Path(
        "pbfbench_"
        + datetime.datetime.now(tz=None).strftime("%Y-%m-%dT%H_%M_%S")  # noqa: DTZ005
        + ".log",
    )


def build_application_only_options(
    connector_type: type[abc_tool_connector.OnlyOptions],
) -> typer.Typer:
    """Build tool application when tool has only options."""
    # FIXME simplify that by generalization
    tool_description = connector_type.description()
    app = typer.Typer(
        name=tool_description.cmd(),
        help=f"Subcommand for tool `{tool_description.name()}`",
        rich_markup_mode="rich",
    )
    run_app = Run(connector_type)
    app.command(name=run_app.NAME, help=run_app.help())(run_app.main)
    config_app = ConfigAppOnlyOptions(connector_type)
    app.command(name=config_app.NAME, help=config_app.help())(config_app.main)
    # TODO add check when ready
    return app


def build_application_with_arguments(
    connector_type: type[abc_tool_connector.WithArguments],
) -> typer.Typer:
    """Build tool application when tool has arguments."""
    # FIXME simplify that by generalization
    tool_description = connector_type.description()
    app = typer.Typer(
        name=tool_description.cmd(),
        help=f"Subcommand for tool `{tool_description.name()}`",
        rich_markup_mode="rich",
    )
    # #
    # # Init and run apps
    # #
    # run_app: _RunAppWithArguments
    # if init_app_type is not None:
    #     init_app = init_app_type(connector_type)
    #     app.command(name=init_app.NAME, help=init_app.help())(init_app.main)
    #     run_app = InitAndRunAppWithArguments(connector_type, init_app.init)
    #     app.command(name=run_app.NAME, help=run_app.help())(run_app.main)
    # else:
    #     run_app = OnlyRunAppWithArguments(connector_type)
    #     app.command(name=run_app.NAME, help=run_app.help())(run_app.main)
    run_app = Run(connector_type)
    app.command(name=run_app.NAME, help=run_app.help())(run_app.main)
    #
    # Config apps
    #
    config_app = ConfigAppWithArguments(connector_type)
    app.command(name=config_app.NAME, help=config_app.help())(config_app.main)
    # TODO add check when ready
    return app


class Arguments:
    """Tool application arguments."""

    EXP_NAME = typer.Argument(
        help="Name of the experiment",
    )

    DATA_DIR = typer.Argument(
        help="Path to the data directory (preferably absolute)",
    )


class RunArgs:
    """Run command arguments."""

    WORK_DIR = typer.Argument(
        help="Path to the working directory (preferably absolute)",
    )
    EXP_CONFIG_YAML = typer.Argument(
        help="Path to the experiment configuration YAML file (preferably absolute)",
    )


class RunOptions:
    """Run command options."""

    # FEATURE Implement run options
    RUN_SUCCESS = typer.Option(
        "--success/--skip-success",
        help="Run the experiment for samples that succeeded",
    )
    RUN_NOT_RUN = typer.Option(
        "--not-run/--skip-not-run",
        help="Run the experiment for samples that were not run (default)",
    )
    RUN_MISSING_INPUTS = typer.Option(
        "--missing-inputs/--skip-missing-inputs",
        help="Run the experiment for samples that have missing inputs",
    )
    RUN_ERROR = typer.Option(
        "--error/--skip-error",
        help="Run the experiment for failed samples",
    )
    RUN_ALL = typer.Option(
        "--all",
        help=(
            "Run the experiment for all samples"
            " (can be completed with other flags to reduce the set of samples to run)"
        ),
    )


class InitAPP(ABC):
    """Init application."""

    # REFACTOR command will disappear

    NAME = abc_app.FinalCommands.INIT

    def __init__(
        self,
        connector: abc_tool_connector.WithArguments,
    ) -> None:
        """Initialize."""
        self.__connector = connector

    def connector(self) -> abc_tool_connector.WithArguments:
        """Get connector."""
        return self.__connector

    def help(self) -> str:
        """Get help string."""
        # FIXME help command will change if init is done during run
        return f"Initialize inputs for {self.__connector.description().name()} tool."

    def main(
        self,
        data_dir: Annotated[Path, Arguments.DATA_DIR],
        work_dir: Annotated[Path, Arguments.WORK_DIR],
        exp_config_yaml: Annotated[Path, Arguments.EXP_CONFIG_YAML],
        debug: Annotated[bool, root_logging.OPT_DEBUG] = False,
    ) -> None:
        """Init tool."""
        root_logging.init_logger(
            _LOGGER,
            "Initialize inputs for the tool",
            debug,
            log_file=log_filename(),
        )

        (data_exp_fs_manager, work_exp_fs_manager, exp_config) = (
            _successfull_check_before_start_or_errror(
                data_dir,
                work_dir,
                exp_config_yaml,
                self.__connector,
            )
        )

        # TODO copy config in data dir (already created it seems)

        self.init(data_exp_fs_manager, work_exp_fs_manager, exp_config)

        typer.Exit(0)

    @abstractmethod
    def init(
        self,
        data_exp_fs_manager: exp_fs.DataManager,
        work_exp_fs_manager: exp_fs.WorkManager,
        config: exp_cfg.WithArguments,
    ) -> None:
        """Init tool."""
        raise NotImplementedError


Connector = TypeVar(
    "Connector",
    bound=abc_tool_connector.OnlyOptions | abc_tool_connector.WithArguments,
)


class Run[C: abc_tool_connector.OnlyOptions | abc_tool_connector.WithArguments]:
    """Run application."""

    NAME = abc_app.FinalCommands.RUN

    def __init__(self, tool_connector_type: type[C]) -> None:
        """Initialize."""
        self._tool_connector_type = tool_connector_type

    def connector_type(self) -> type[C]:
        """Get connector."""
        return self._tool_connector_type

    def help(self) -> str:
        """Get help string."""
        return f"Run {self._tool_connector_type.description().name()} tool."

    def main(  # noqa: PLR0913
        self,
        exp_name: Annotated[str, Arguments.EXP_NAME],
        data_dir: Annotated[Path, Arguments.DATA_DIR],
        work_dir: Annotated[Path, RunArgs.WORK_DIR],
        exp_config_yaml: Annotated[Path, RunArgs.EXP_CONFIG_YAML],
        run_success: Annotated[bool, RunOptions.RUN_SUCCESS] = False,
        run_not_run: Annotated[bool, RunOptions.RUN_NOT_RUN] = True,
        run_missing_inputs: Annotated[bool, RunOptions.RUN_MISSING_INPUTS] = False,
        run_error: Annotated[bool, RunOptions.RUN_ERROR] = False,
        run_all: Annotated[bool, RunOptions.RUN_ALL] = False,
        debug: Annotated[bool, root_logging.OPT_DEBUG] = False,
    ) -> None:
        """Run tool."""
        root_logging.init_logger(_LOGGER, "Run tool", debug, log_file=log_filename())

        exp_manager = self._successfull_check_before_start_or_errror(
            exp_name,
            data_dir,
            work_dir,
            exp_config_yaml,
        )
        self._error_if_experiment_is_running(exp_manager)

        exp_run.start_new_experiment(
            exp_manager,
            self._target_samples_to_run(
                run_success,
                run_not_run,
                run_missing_inputs,
                run_error,
                run_all,
            ),
            self._format_inputs,
        )
        # FIXME put here end print stats function
        # _LOGGER.info(
        #     "Total number of samples: %d\n"
        #     "* Number of already done samples: %d\n"
        #     "* Number of running samples: %d\n"
        #     "  * Number of successfully run samples: %d\n"
        #     "  * Number of samples which exit with errors: %d\n",
        #     run_stats.number_of_samples(),
        #     run_stats.number_of_samples() - run_stats.number_of_samples_to_run(),
        #     run_stats.number_of_samples_to_run(),
        #     run_stats.number_of_samples_to_run() - len(run_stats.samples_with_errors()),
        #     len(run_stats.samples_with_errors()),
        # )
        raise typer.Exit(0)

    def _error_if_experiment_is_running(
        self,
        exp_manager: exp_managers.WithOptions,
    ) -> None:
        """Exit with error if the experiment is already running."""
        match running_exp := exp_checks.experiment_is_running(
            exp_manager.data_fs_manager(),
        ):
            case exp_checks.RunningExperiment():
                _LOGGER.critical(
                    "The experiment is already in progress\n"
                    "* Experiment launched the: %s\n"
                    "* Working directory root path: %s\n"
                    "* SLURM job ID: %s\n"
                    "* SACCT state: %s\n",
                    running_exp.in_progress_data().date(),
                    running_exp.in_progress_data().working_directory(),
                    running_exp.in_progress_data().job_id(),
                    running_exp.sacct_state(),
                )
                _LOGGER.info("You must use the `resume` command")
                raise typer.Exit(1)

    def _format_inputs(self, exp_manager: exp_managers.WithArguments) -> None:
        """Format inputs."""

    def _successfull_check_before_start_or_errror(
        self,
        exp_name: str,
        data_dir: Path,
        work_dir: Path,
        tool_config_yaml: Path,
    ) -> exp_managers.OnlyOptions | exp_managers.WithArguments:
        #
        # Resolve absolute paths
        #
        data_dir = data_dir.resolve()
        work_dir = work_dir.resolve()
        tool_config_yaml = tool_config_yaml.resolve()

        match check_result := exp_checks.check_before_start(
            exp_name,
            data_dir,
            work_dir,
            tool_config_yaml,
            self._tool_connector_type,
        ):
            case exp_checks.RunOK():
                return check_result.exp_manager()
            case exp_checks.RunErrors():
                _LOGGER.critical("The experiment checkers found errors")
                raise typer.Exit(1)

    def _target_samples_to_run(
        self,
        run_success: bool,
        run_not_run: bool,
        run_missing_inputs: bool,
        run_error: bool,
        run_all: bool,
    ) -> Callable[[smp_status.Status], bool]:
        targets_to_run_filter: dict[smp_status.Status, bool] = dict.fromkeys(
            (
                smp_status.OK.OK,
                smp_status.Error.NOT_RUN,
                smp_status.Error.MISSING_INPUTS,
                smp_status.Error.ERROR,
            ),
            run_all,
        )
        if not run_all:
            targets_to_run_filter[smp_status.OK.OK] = run_success
            targets_to_run_filter[smp_status.Error.NOT_RUN] = run_not_run
            targets_to_run_filter[smp_status.Error.MISSING_INPUTS] = run_missing_inputs
            targets_to_run_filter[smp_status.Error.ERROR] = run_error
        return lambda status: targets_to_run_filter[status]


class ResumeOpts:
    """Resume command options."""

    # FEATURE add resume options
    EXP_NAME = typer.Option(
        "--name",
        "-n",
        help="Name of the experiment to resume.",
    )
    CONFIG_YAML = typer.Option(
        "--config",
        "-c",
        help="Path to the experiment configuration YAML file.",
    )


class ResumeApp[C: abc_tool_connector.WithOptions]:
    """Resume application base class."""

    NAME = "resume"

    def __init__(self, connector: C) -> None:
        """Initialize."""
        self._connector = connector

    def main(
        self,
        data_dir: Annotated[Path, Arguments.DATA_DIR],
        exp_name: Annotated[str | None, ResumeOpts.EXP_NAME] = None,
        config_yaml: Annotated[Path | None, ResumeOpts.CONFIG_YAML] = None,
        debug: Annotated[bool, root_logging.OPT_DEBUG] = False,
    ) -> None:
        """Resume the tool jobs."""
        root_logging.init_logger(
            _LOGGER,
            "Resume tool jobs",
            debug,
            log_file=log_filename(),
        )

        # TODO continue here

        # REFACTOR ugly if-else because of exp_config type (see todos file for details)
        exp_config: exp_cfg.WithOptions
        if isinstance(self._connector, abc_tool_connector.OnlyOptions):
            (data_exp_fs_manager, work_exp_fs_manager, exp_config) = (
                _check_experiment_success_only_options(
                    data_dir,
                    work_dir,
                    exp_config_yaml,
                    self._connector,
                )
            )
        elif isinstance(self._connector, abc_tool_connector.WithArguments):
            (data_exp_fs_manager, work_exp_fs_manager, exp_config) = (
                _successfull_check_before_start_or_errror(
                    data_dir,
                    work_dir,
                    exp_config_yaml,
                    self._connector,
                )
            )
        else:
            _LOGGER.critical("Unsupported connector type: %s", type(self._connector))
            raise typer.Exit(1)
        # REFACTOR wrap in a function with Typer.Exit
        exp_checks.compare_config_vs_config_in_data(
            work_exp_fs_manager,
            exp_config,
        )

        # TODO [!] unfinished todos
        # TODO merge with run cmd:
        # * verify if experiment is running -> complete
        # * otherwise -> init run and complete
        # REFACTOR do not use stats as an object:
        # * Read stats from file system (errors.tsv etc.)
        # FIXME tmp fix for mypy
        not_finished_samples: list[smp_fs.RowNumberedItem] = []
        exp_complete.complete_experiment(
            not_finished_samples,
            data_exp_fs_manager,
            work_exp_fs_manager,
        )

        raise typer.Exit(0)

    def help(self) -> str:
        """Get help string."""
        return (
            f"Complete pbfbench jobs for {self._connector.description().name()} tool."
        )


class ConfigAppWithOptions[
    Connector: abc_tool_connector.WithOptions,
    Config: abc_tool_cfg.WithOptions,
](ABC):
    """Config application base class."""

    NAME = "config"

    def __init__(self, connector_type: type[Connector]) -> None:
        """Initialize."""
        self._connector_type = connector_type

    def connector_type(self) -> type[Connector]:
        """Get connector."""
        return self._connector_type

    def help(self) -> str:
        """Get help string."""
        return (
            "Get draft "
            + self._connector_type.description().name()
            + " tool configuration."
        )

    def main(
        self,
        config_exp_yaml: Annotated[Path, RunArgs.EXP_CONFIG_YAML],
        debug: Annotated[bool, root_logging.OPT_DEBUG] = False,
    ) -> None:
        """Get draft config."""
        root_logging.init_logger(
            _LOGGER,
            "Generating a configuration file draft"
            f" for topic: {self._connector_type.description().topic().name()}"
            f" tool: {self._connector_type.description().name()}",
            debug,
        )

        config = self._fake_config()

        config.to_yaml(config_exp_yaml)
        _LOGGER.info("Tool configuration written to %s", config_exp_yaml)

    @abstractmethod
    def _fake_config(self) -> Config:
        """Create fake tool config."""
        raise NotImplementedError

    def _fake_options_config(self) -> abc_tool_cfg.StringOpts:
        return abc_tool_cfg.StringOpts(
            ("--options1=value1", "--options2=value2"),
        )

    def _create_slurm_cfg(self) -> slurm_cfg.Config:
        # FIXME move slurm config generator elsewhere
        return slurm_cfg.Config(
            [
                "--mem=4096",
                "--cpus-per-task=4",
                "--time=1:00:00",
                "--account=my-account_name",
            ],
        )


@final
class ConfigAppOnlyOptions(
    ConfigAppWithOptions[abc_tool_connector.OnlyOptions, abc_tool_cfg.OnlyOptions],
):
    """Config application for tools with only options."""

    def _fake_config(self) -> abc_tool_cfg.OnlyOptions:
        return self._connector_type.config_type()(self._fake_options_config())


@final
class ConfigAppWithArguments(
    ConfigAppWithOptions[abc_tool_connector.WithArguments, abc_tool_cfg.WithArguments],
):
    """Config application for tools with arguments."""

    def _fake_config(self) -> abc_tool_cfg.WithArguments:
        return self._connector_type.config_type()(
            self._fake_arguments_config(),
            self._fake_options_config(),
        )

    def _fake_arguments_config(self) -> abc_tool_cfg.Arguments:
        """Create arguments."""
        args: dict[str, abc_tool_cfg.Arg] = {}
        for arg_type in self._connector_type.arguments_type().arg_types():
            tool_choice_str = " | ".join(map(str, arg_type.valid_tools()))
            args[str(arg_type.name())] = abc_tool_cfg.Arg(
                tool_choice_str,
                "$input_experiment_name",
            )
        return abc_tool_cfg.Arguments(args)
