"""Experiment checking module."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import TYPE_CHECKING, cast

import pbfbench.abc.tool.config as abc_tool_cfg
import pbfbench.abc.tool.connector as abc_tool_connector
import pbfbench.slurm.bash as slurm_bash

from . import file_system as exp_fs
from . import in_progress
from . import managers as exp_managers

if TYPE_CHECKING:
    from pathlib import Path

    from pbfbench.slurm import sacct

_LOGGER = logging.getLogger(__name__)


class RunOK[M: exp_managers.WithOptions]:
    """OK status."""

    def __init__(self, exp_manager: M) -> None:
        self._exp_manager = exp_manager

    def exp_manager(self) -> M:
        """Get experiment manager."""
        return self._exp_manager


class RunErrors(StrEnum):
    """Experiment checks error status before run."""

    NO_PERMISSION = "no_permission"
    READ_CONFIG_FAILED = "read_config_failed"
    MISSING_TOOL_ENV_WRAPPER_SCRIPT = "missing_tool_env_wrapper_script"


def check_before_start(
    exp_name: str,
    data_dir: Path,
    work_dir: Path,
    tool_config_yaml: Path,
    tool_connector_type: type[
        abc_tool_connector.OnlyOptions | abc_tool_connector.WithArguments
    ],
) -> RunOK[exp_managers.OnlyOptions | exp_managers.WithArguments] | RunErrors:
    """Check experiment."""
    match _check_read_write_access(data_dir, work_dir):
        case PermissionErrors():
            return RunErrors.NO_PERMISSION

    connector_or_error = _instantiate_connector(tool_connector_type, tool_config_yaml)

    match connector_or_error:
        case RunErrors():
            return connector_or_error

    _LOGGER.debug(
        "Experiment config:\n%s",
        connector_or_error.to_config().to_yaml_dump(),
    )

    exp_manager = _get_exp_manager(exp_name, data_dir, work_dir, connector_or_error)

    if _missing_env_wrapper_script(exp_manager.data_fs_manager()):
        return RunErrors.MISSING_TOOL_ENV_WRAPPER_SCRIPT

    return RunOK(exp_manager)


class PermissionOK(StrEnum):
    """Permission OK status."""

    READ_WRITE = "read_write"


class PermissionErrors(StrEnum):
    """Permission status."""

    NO_READ_ACCESS = "no_read_access"
    NO_WRITE_ACCESS = "no_write_access"


type PermissionStatus = PermissionOK | PermissionErrors


def _check_read_write_access(data_dir: Path, work_dir: Path) -> PermissionStatus:
    """Check read and write access."""
    match status := _check_read_write_access_data(data_dir):
        case PermissionErrors():
            return status

    match status := _check_read_write_access_work(work_dir):
        case PermissionErrors():
            return status

    return PermissionOK.READ_WRITE


def _check_read_write_access_data(data_dir: Path) -> PermissionStatus:
    """Check read and write access."""
    if not data_dir.exists():
        _LOGGER.critical("Data directory %s does not exist", data_dir)
        return PermissionErrors.NO_READ_ACCESS

    file_test = data_dir / "test_read_write.txt"
    try:
        file_test.write_text("test")
    except OSError as err:
        _LOGGER.critical("No write access to %s with exception: %s", data_dir, err)
        return PermissionErrors.NO_WRITE_ACCESS

    try:
        file_test.read_text()
    except OSError as err:
        _LOGGER.critical("No read access to %s with exception: %s", data_dir, err)
        file_test.unlink()
        return PermissionErrors.NO_READ_ACCESS

    file_test.unlink()

    return PermissionOK.READ_WRITE


def _check_read_write_access_work(work_dir: Path) -> PermissionStatus:
    """Check read and write access."""
    try:
        work_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        _LOGGER.exception("No write access to %s", work_dir)
        return PermissionErrors.NO_WRITE_ACCESS
    file_test = work_dir / "test_read_write.txt"

    try:
        file_test.write_text("test")
    except OSError:
        _LOGGER.exception("No write access to %s", work_dir)
        file_test.unlink(missing_ok=True)
        if not any(work_dir.iterdir()):
            work_dir.rmdir()
        return PermissionErrors.NO_WRITE_ACCESS

    try:
        file_test.read_text()
    except OSError:
        _LOGGER.exception("No read access to %s", work_dir)
        file_test.unlink()
        if not any(work_dir.iterdir()):
            work_dir.rmdir()
        return PermissionErrors.NO_READ_ACCESS

    file_test.unlink()
    if not any(work_dir.iterdir()):
        work_dir.rmdir()

    return PermissionOK.READ_WRITE


def _instantiate_connector(
    tool_connector_type: type[
        abc_tool_connector.OnlyOptions | abc_tool_connector.WithArguments
    ],
    tool_config_yaml: Path,
) -> abc_tool_connector.OnlyOptions | abc_tool_connector.WithArguments | RunErrors:
    if tool_connector_type is abc_tool_connector.OnlyOptions:
        tool_connector_type = cast(
            "type[abc_tool_connector.OnlyOptions]",
            tool_connector_type,
        )  # Mypy fails to infer otherwise
        return tool_connector_type.from_config(
            abc_tool_cfg.OnlyOptions.from_yaml(tool_config_yaml),
        )
    tool_connector_type = cast(
        "type[abc_tool_connector.WithArguments]",
        tool_connector_type,
    )  # Mypy fails to infer otherwise
    match connector_or_error := tool_connector_type.from_config(
        abc_tool_cfg.WithArguments.from_yaml(tool_config_yaml),
    ):
        case abc_tool_connector.InvalidToolNameError():
            _LOGGER.critical(
                "Invalid tool name `%s` for argument name `%s`."
                " Choose among the valid tools in : {%s}",
                connector_or_error.invalid_tool_name(),
                connector_or_error.arg_name(),
                ", ".join(connector_or_error.valid_tools()),
            )
            return RunErrors.READ_CONFIG_FAILED
        case abc_tool_connector.MissingArgumentNameError():
            _LOGGER.critical(
                "Argument name not found: `%s`."
                " All the argument names must be present: {%s}",
                connector_or_error.missing_arg_name(),
                ", ".join(str(name) for name in connector_or_error.names_type()),
            )
            return RunErrors.READ_CONFIG_FAILED
        case abc_tool_connector.ExtraArgumentNameError():
            _LOGGER.critical(
                "Extra argument name: `%s`."
                " Only argument names in the following set must be present: {%s}",
                connector_or_error.extra_arg_names(),
                ", ".join(str(name) for name in connector_or_error.names_type()),
            )
            return RunErrors.READ_CONFIG_FAILED
    return connector_or_error


def _get_exp_manager(
    exp_name: str,
    data_dir: Path,
    work_dir: Path,
    connector: abc_tool_connector.OnlyOptions | abc_tool_connector.WithArguments,
) -> exp_managers.OnlyOptions | exp_managers.WithArguments:
    data_exp_fs_manager, work_exp_fs_manager = exp_fs.data_and_working_managers(
        data_dir,
        work_dir,
        connector.description(),
        exp_name,
    )
    match connector:
        case abc_tool_connector.OnlyOptions():
            return exp_managers.OnlyOptions(
                exp_name,
                data_exp_fs_manager,
                work_exp_fs_manager,
                connector,
            )
        case abc_tool_connector.WithArguments():
            return exp_managers.WithArguments(
                exp_name,
                data_exp_fs_manager,
                work_exp_fs_manager,
                connector,
            )


def _missing_env_wrapper_script(data_exp_fs_manager: exp_fs.DataManager) -> bool:
    """Check missing env wrapper script."""
    if not data_exp_fs_manager.tool_env_script_sh().exists():
        _LOGGER.critical("Missing tool environment wrapper script")
        # TODO add help here (propose command to print script with requirements)
        return True
    return False


class RunningExperiment:
    """Running experiment metadata."""

    def __init__(
        self,
        in_progress_data: in_progress.InDataDirectory,
        sacct_state: sacct.State | None,
    ) -> None:
        self._in_progress_data = in_progress_data
        self._sacct_state = sacct_state

    def in_progress_data(self) -> in_progress.InDataDirectory:
        """Get in progress metadata in the data directory."""
        return self._in_progress_data

    def sacct_state(self) -> sacct.State | None:
        """Get sacct state."""
        return self._sacct_state


def experiment_is_running(
    data_exp_fs_manager: exp_fs.DataManager,
) -> None | RunningExperiment:
    """Check if experiment is running."""
    if not data_exp_fs_manager.in_progress_yaml().exists():
        return None

    in_progress_data = in_progress.InDataDirectory.from_yaml(
        data_exp_fs_manager.in_progress_yaml(),
    )
    return RunningExperiment(
        in_progress_data,
        slurm_bash.get_state(in_progress_data.job_id()),
    )


class SameExperimentConfigs(StrEnum):
    """Same experiment configs OK status."""

    SAME = "same"


class DifferentExperimentConfigs(StrEnum):
    """Different experiment configs error."""

    DIFFERENT_SYNTAX = "different_syntax"
    NOT_SAME = "not_same"


type ExperimentConfigComparison = SameExperimentConfigs | DifferentExperimentConfigs


def compare_config_vs_config_in_data(
    connector: abc_tool_connector.OnlyOptions | abc_tool_connector.WithArguments,
    config_in_data_yaml: Path,
) -> ExperimentConfigComparison:
    """Compare two experimentation configs."""
    connector_in_data: (
        abc_tool_connector.OnlyOptions
        | abc_tool_connector.WithArguments
        | abc_tool_connector.ArgsLoadError
    )
    match connector:
        case abc_tool_connector.OnlyOptions():
            connector_in_data = abc_tool_connector.OnlyOptions.from_config(
                abc_tool_cfg.OnlyOptions.from_yaml(config_in_data_yaml),
            )
        case abc_tool_connector.WithArguments():
            match connector_in_data := type(connector).from_config(
                abc_tool_cfg.WithArguments.from_yaml(config_in_data_yaml),
            ):
                case (
                    abc_tool_connector.InvalidToolNameError()
                    | abc_tool_connector.MissingArgumentNameError()
                    | abc_tool_connector.ExtraArgumentNameError()
                ):
                    return DifferentExperimentConfigs.DIFFERENT_SYNTAX

    match connector:  # force for type checking
        case abc_tool_connector.OnlyOptions():
            connector_in_data = cast(
                "abc_tool_connector.OnlyOptions",
                connector_in_data,
            )
            is_same = connector.is_same(connector_in_data)
        case abc_tool_connector.WithArguments():
            connector_in_data = cast(
                "abc_tool_connector.WithArguments",
                connector_in_data,
            )
            is_same = connector.is_same(connector_in_data)

    if not is_same:
        _LOGGER.critical(
            "Existing and given experiment configurations are not the same",
        )
        return DifferentExperimentConfigs.NOT_SAME

    return SameExperimentConfigs.SAME
