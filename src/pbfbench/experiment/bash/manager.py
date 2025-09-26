"""Experiment bash manager."""

from __future__ import annotations

import pbfbench.experiment.in_progress as exp_in_progress
import pbfbench.experiment.managers as exp_managers

from . import file_system as fs


class Manager:
    """Experiment bash manager."""

    @classmethod
    def from_exp_fs_manager(
        cls,
        exp_fs_manager: exp_managers.OnlyOptions | exp_managers.WithArguments,
    ) -> Manager:
        """Initialize from experiment file system manager."""
        date_str = exp_in_progress.get_today_format_string()
        return cls(
            exp_fs_manager.data_fs_manager().scripts_fs_manager(date_str),
            exp_fs_manager.work_fs_manager().scripts_fs_manager(date_str),
        )

    def __init__(
        self,
        data_sh_fs_manager: fs.Manager,
        work_sh_fs_manager: fs.Manager,
    ) -> None:
        self.__data_sh_fs_manager = data_sh_fs_manager
        self.__work_sh_fs_manager = work_sh_fs_manager

    def data_sh_fs_manager(self) -> fs.Manager:
        """Get data shell file system manager."""
        return self.__data_sh_fs_manager

    def work_sh_fs_manager(self) -> fs.Manager:
        """Get working shell file system manager."""
        return self.__work_sh_fs_manager
