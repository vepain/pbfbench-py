"""Experiment checking module."""

from __future__ import annotations

import logging
from enum import StrEnum
from pathlib import Path

import pbfbench.abc.tool.config as abc_tool_config
import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.experiment.config as exp_cfg
import pbfbench.experiment.file_system as exp_fs

_LOGGER = logging.getLogger(__name__)


class _OK[ExpConfig: exp_cfg.ConfigWithOptions]:
    """OK status."""

    def __init__(
        self,
        data_exp_fs_manager: exp_fs.DataManager,
        work_exp_fs_manager: exp_fs.WorkManager,
        exp_config: ExpConfig,
    ) -> None:
        self._data_exp_fs_manager = data_exp_fs_manager
        self._work_exp_fs_manager = work_exp_fs_manager
        self._exp_config = exp_config

    def data_exp_fs_manager(self) -> exp_fs.DataManager:
        """Get data experiment file system manager."""
        return self._data_exp_fs_manager

    def work_exp_fs_manager(self) -> exp_fs.WorkManager:
        """Get working experiment file system manager."""
        return self._work_exp_fs_manager

    def exp_config(self) -> ExpConfig:
        """Get experiment config."""
        return self._exp_config


class OKOnlyOptions(_OK[exp_cfg.ConfigOnlyOptions]):
    """OK status for tools with only options."""


class OKWithArguments(_OK[exp_cfg.ConfigWithArguments]):
    """OK status for tools with arguments."""


class ErrorOnlyOptions(StrEnum):
    """Experiment checks error status for tools with only options."""

    NO_PERMISSION = "no_permission"
    READ_CONFIG_FAILED = "read_config_failed"
    MISSING_TOOL_ENV_WRAPPER_SCRIPT = "missing_tool_env_wrapper_script"
    DIFFERENT_CONFIGURATIONS = "different_configurations"


class ErrorsWithArguments(StrEnum):
    """Experiment checks error status for tools with arguments."""

    NO_PERMISSION = "no_permission"
    READ_CONFIG_FAILED = "read_config_failed"
    WRONG_INPUT_TOOLS = "wrong_input_tools"
    MISSING_TOOL_ENV_WRAPPER_SCRIPT = "missing_tool_env_wrapper_script"
    DIFFERENT_CONFIGURATIONS = "different_configurations"


def check_experiment_with_only_options(
    data_dir: Path,
    work_dir: Path,
    exp_config_yaml: Path,
    tool_connector: abc_tool_visitor.ConnectorOnlyOptions,
) -> OKOnlyOptions | ErrorOnlyOptions:
    """Check experiment."""
    match _check_read_write_access(data_dir, work_dir):
        case PermissionErrors():
            return ErrorOnlyOptions.NO_PERMISSION

    try:
        exp_config = tool_connector.read_config(exp_config_yaml)
    except Exception:  # noqa: BLE001
        return ErrorOnlyOptions.READ_CONFIG_FAILED

    _LOGGER.debug("Experiment config:\n%s", exp_config.to_yaml_dump())

    data_exp_fs_manager, work_exp_fs_manager = exp_fs.data_and_working_managers(
        data_dir,
        work_dir,
        tool_connector.description(),
        exp_config.name(),
    )

    if _missing_env_wrapper_script(data_exp_fs_manager):
        return ErrorOnlyOptions.MISSING_TOOL_ENV_WRAPPER_SCRIPT

    if data_exp_fs_manager.config_yaml().exists():
        match _is_same_experiment(data_exp_fs_manager, exp_config):
            case SameExperimentErrors():
                return ErrorOnlyOptions.DIFFERENT_CONFIGURATIONS

    return OKOnlyOptions(data_exp_fs_manager, work_exp_fs_manager, exp_config)


def check_experiment_with_arguments[
    N: abc_tool_config.Names,
    ExpConfig: exp_cfg.ConfigWithArguments,
](
    data_dir: Path,
    work_dir: Path,
    exp_config_yaml: Path,
    tool_connector: abc_tool_visitor.ConnectorWithArguments[N, ExpConfig],
) -> OKWithArguments | ErrorsWithArguments:
    """Check experiment."""
    match _check_read_write_access(data_dir, work_dir):
        case PermissionErrors():
            return ErrorsWithArguments.NO_PERMISSION

    try:
        exp_config = tool_connector.read_config(exp_config_yaml)
    except Exception:
        _LOGGER.exception("Failed to read experiment config:")
        return ErrorsWithArguments.READ_CONFIG_FAILED

    _LOGGER.debug("Experiment config:\n%s", exp_config.to_yaml_dump())

    if not _check_config_inputs(exp_config, tool_connector):
        return ErrorsWithArguments.WRONG_INPUT_TOOLS

    data_exp_fs_manager, work_exp_fs_manager = exp_fs.data_and_working_managers(
        data_dir,
        work_dir,
        tool_connector.description(),
        exp_config.name(),
    )

    if _missing_env_wrapper_script(data_exp_fs_manager):
        return ErrorsWithArguments.MISSING_TOOL_ENV_WRAPPER_SCRIPT

    if data_exp_fs_manager.config_yaml().exists():
        match _is_same_experiment(data_exp_fs_manager, exp_config):
            case SameExperimentErrors():
                return ErrorsWithArguments.DIFFERENT_CONFIGURATIONS

    return OKWithArguments(data_exp_fs_manager, work_exp_fs_manager, exp_config)


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
        _LOGGER.error("Data directory %s does not exist", data_dir)
        return PermissionErrors.NO_READ_ACCESS

    file_test = data_dir / "test_read_write.txt"
    try:
        file_test.write_text("test")
    except OSError:
        _LOGGER.exception("No write access to %s", data_dir)
        return PermissionErrors.NO_WRITE_ACCESS

    try:
        file_test.read_text()
    except OSError:
        _LOGGER.exception("No read access to %s", data_dir)
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


def _check_config_inputs(
    config: exp_cfg.ConfigWithArguments,
    connector: abc_tool_visitor.ConnectorWithArguments,
) -> bool:
    """Check config inputs."""
    value_errors = connector.check_arguments_implement_results(config)
    for value_error in value_errors:
        _LOGGER.critical(str(value_error))
    return not value_errors


def _missing_env_wrapper_script(data_exp_fs_manager: exp_fs.DataManager) -> bool:
    """Check missing env wrapper script."""
    if not data_exp_fs_manager.tool_env_script_sh().exists():
        _LOGGER.error("Missing tool env wrapper script")
        # TODO add help here (propose command to print script with requirements)
        return True
    return False


class SameExperimentOK(StrEnum):
    """Same experiment OK status."""

    SAME = "same"


class SameExperimentErrors(StrEnum):
    """Same experiment error."""

    SAME = "same"
    DIFFERENT_SYNTAX = "different_syntax"
    NOT_SAME = "not_same"


type SameExperimentStatus = SameExperimentOK | SameExperimentErrors


def _is_same_experiment(
    data_exp_fs_manager: exp_fs.DataManager,
    config: exp_cfg.ConfigWithOptions,
) -> SameExperimentStatus:
    """Check if experiment is the same."""
    try:
        config_in_data = type(config).from_yaml(
            data_exp_fs_manager.config_yaml(),
        )
    except Exception:
        _LOGGER.exception(
            "Existing and given experiment configurations are not of the same type",
        )
        return SameExperimentErrors.DIFFERENT_SYNTAX

    if not config.is_same(config_in_data):
        _LOGGER.error(
            "Existing and given experiment configurations are not the same",
        )
        return SameExperimentErrors.NOT_SAME

    return SameExperimentOK.SAME
