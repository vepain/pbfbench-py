"""Tool abstract application module."""

# Due to typer usage:
# ruff: noqa: TC003, FBT002, FBT001

from __future__ import annotations

import datetime
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, TypeVar, cast, final

import typer

import pbfbench.abc.app as abc_app
import pbfbench.experiment.checks as exp_checks
import pbfbench.experiment.file_system as exp_fs
import pbfbench.experiment.in_progress as exp_in_progress
import pbfbench.experiment.managers as exp_managers
import pbfbench.experiment.resume as exp_resume
import pbfbench.experiment.run as exp_run
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


def build_application(
    connector_type: type[
        abc_tool_connector.OnlyOptions | abc_tool_connector.WithArguments
    ],
) -> typer.Typer:
    """Build tool application."""
    tool_description = connector_type.description()
    app = typer.Typer(
        name=tool_description.cmd(),
        help=f"Subcommand for tool `{tool_description.name()}`",
        rich_markup_mode="rich",
    )
    #
    # Run app
    #
    run_app = Run(connector_type)
    app.command(name=run_app.NAME, help=run_app.help())(run_app.main)
    #
    # Resume app
    #
    resume_app = Resume(connector_type)
    app.command(name=resume_app.NAME, help=resume_app.help())(resume_app.main)
    #
    # Config app
    #
    config_app: ConfigAppWithOptions
    if connector_type is abc_tool_connector.OnlyOptions:
        config_app = ConfigAppOnlyOptions(
            cast("type[abc_tool_connector.OnlyOptions]", connector_type),
        )
    else:
        config_app = ConfigAppWithArguments(
            cast("type[abc_tool_connector.WithArguments]", connector_type),
        )
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
    SLURM_OPTIONS = typer.Option(
        "--slurm-opts",
        help="SLURM options",
    )


Connector = TypeVar(
    "Connector",
    bound=abc_tool_connector.OnlyOptions | abc_tool_connector.WithArguments,
)


class Run[
    CType: type[abc_tool_connector.OnlyOptions | abc_tool_connector.WithArguments],
]:
    """Run application."""

    NAME = abc_app.FinalCommands.RUN

    def __init__(
        self,
        tool_connector_type: CType,
    ) -> None:
        """Initialize."""
        self._tool_connector_type = tool_connector_type

    def connector_type(
        self,
    ) -> CType:
        """Get connector."""
        return self._tool_connector_type

    def help(self) -> str:
        """Get help string."""
        return (
            "Run"
            f" {self.connector_type().description().name()}"
            f" ({self.connector_type().description().topic().name()}) tool."
        )

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
        slurm_opts: Annotated[str | None, RunOptions.SLURM_OPTIONS] = None,
        debug: Annotated[bool, root_logging.OPT_DEBUG] = False,
    ) -> None:
        """Run tool."""
        root_logging.init_logger(
            _LOGGER,
            (
                f"Run experiment `{exp_name}`"
                f" for tool {self.connector_type().description().name()}"
                f" for topic {self.connector_type().description().topic().name()}"
            ),
            debug,
            log_file=log_filename(),
        )

        exp_manager = self._successfull_check_before_start_or_errror(
            exp_name,
            data_dir,
            work_dir,
            exp_config_yaml,
        )
        self._error_if_experiment_is_running(exp_manager)

        if slurm_opts is None:
            slurm_opts = slurm_cfg.default_slurm_options(None)

        exp_run.start_new_experiment(
            exp_manager,
            self._target_samples_to_run(
                run_success,
                run_not_run,
                run_missing_inputs,
                run_error,
                run_all,
            ),
            slurm_opts,
        )
        # FIXME put here end print stats function
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


class Resume[
    CType: (type[abc_tool_connector.OnlyOptions | abc_tool_connector.WithArguments]),
]:
    """Resume application class."""

    NAME = "resume"

    def __init__(
        self,
        tool_connector_type: CType,
    ) -> None:
        """Initialize."""
        self._tool_connector_type: CType = tool_connector_type

    def connector_type(
        self,
    ) -> CType:
        """Get connector."""
        return self._tool_connector_type

    def main(
        self,
        exp_name: Annotated[str, Arguments.EXP_NAME],
        data_dir: Annotated[Path, Arguments.DATA_DIR],
        debug: Annotated[bool, root_logging.OPT_DEBUG] = False,
    ) -> None:
        """Resume the tool jobs."""
        root_logging.init_logger(
            _LOGGER,
            (
                f"Resume experiment `{exp_name}`"
                f" for tool {self.connector_type().description().name()}"
                f" for topic {self.connector_type().description().topic().name()}"
            ),
            debug,
            log_file=log_filename(),
        )

        exp_manager, array_job_id = self._retrieve_exp_manager_array_job_id(
            exp_name,
            data_dir,
        )

        exp_resume.resume(exp_manager, array_job_id)

        raise typer.Exit(0)

    def _retrieve_exp_manager_array_job_id(
        self,
        exp_name: str,
        data_dir: Path,
    ) -> tuple[exp_managers.OnlyOptions | exp_managers.WithArguments, str]:
        #
        # Resolve absolute paths
        #
        data_fs_manager = exp_fs.DataManager(
            data_dir.resolve(),
            self.connector_type().description(),
            exp_name,
        )
        if not data_fs_manager.in_progress_yaml().exists():
            _LOGGER.critical(
                "The experiment `%s` is not in progress for the data directory `%s`",
                exp_name,
                data_fs_manager.root_dir(),
            )
            raise typer.Exit(1)
        data_in_progress = exp_in_progress.InDataDirectory.from_yaml(
            data_fs_manager.in_progress_yaml(),
        )
        work_fs_manager = exp_fs.WorkManager(
            data_in_progress.working_directory(),
            self.connector_type().description(),
            exp_name,
        )
        connector = exp_checks.instantiate_connector(
            self.connector_type(),
            data_fs_manager.config_yaml(),
        )
        match connector:
            case abc_tool_connector.OnlyOptions():
                return exp_managers.OnlyOptions(
                    exp_name,
                    data_fs_manager,
                    work_fs_manager,
                    connector,
                ), data_in_progress.job_id()
            case abc_tool_connector.WithArguments():
                return exp_managers.WithArguments(
                    exp_name,
                    data_fs_manager,
                    work_fs_manager,
                    connector,
                ), data_in_progress.job_id()
            case exp_checks.RunErrors():
                _LOGGER.critical("Cannot instantiate connector")
                raise typer.Exit(1)

    def help(self) -> str:
        """Get help string."""
        return (
            "Complete pbfbench jobs for"
            f" {self.connector_type().description().name()}"
            f" ({self.connector_type().description().topic().name()}) tool."
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
            if not tool_choice_str:
                tool_choice_str = "ERROR: no tool implements this argument"
            args[str(arg_type.name())] = abc_tool_cfg.Arg(
                tool_choice_str,
                "$input_experiment_name",
            )
        return abc_tool_cfg.Arguments(args)
