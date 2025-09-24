"""Experiment managers."""

from __future__ import annotations

from typing import final

import pbfbench.abc.tool.connector as abc_tool_connector
import pbfbench.experiment.file_system as exp_fs


class WithOptions[C: abc_tool_connector.WithOptions]:
    """Experiment manager."""

    def __init__(
        self,
        exp_name: str,
        data_exp_fs_manager: exp_fs.DataManager,
        work_exp_fs_manager: exp_fs.WorkManager,
        tool_connector: C,
    ) -> None:
        self._exp_name = exp_name
        self._data_exp_fs_manager = data_exp_fs_manager
        self._work_exp_fs_manager = work_exp_fs_manager
        self._tool_connector = tool_connector

    def exp_name(self) -> str:
        """Get experiment name."""
        return self._exp_name

    def data_fs_manager(self) -> exp_fs.DataManager:
        """Get data file system manager."""
        return self._data_exp_fs_manager

    def work_fs_manager(self) -> exp_fs.WorkManager:
        """Get working file system manager."""
        return self._work_exp_fs_manager

    def tool_connector(self) -> C:
        """Get tool connector."""
        return self._tool_connector


@final
class OnlyOptions(WithOptions[abc_tool_connector.OnlyOptions]):
    """Experiment manager with only options."""


@final
class WithArguments(WithOptions[abc_tool_connector.WithArguments]):
    """Experiment manager with arguments."""
