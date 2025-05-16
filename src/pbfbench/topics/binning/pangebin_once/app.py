"""Concrete tool application module."""

# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

from typing import final

import pbfbench.abc.tool.app as abc_tool_app
import pbfbench.experiment.config as exp_cfg
import pbfbench.experiment.file_system as exp_fs
import pbfbench.topics.binning.pangebin_once.init as pangebin_once_init
import pbfbench.topics.binning.pangebin_once.visitor as pangebin_once_visitor


@final
class InitApp(abc_tool_app.InitAPP):
    """Init application."""

    def init(
        self,
        data_exp_fs_manager: exp_fs.DataManager,
        _: exp_fs.WorkManager,
        config: exp_cfg.ConfigWithArguments,
    ) -> None:
        """Init tool."""
        init_stats = pangebin_once_init.init(
            data_exp_fs_manager,
            config,
            self.connector(),
        )


APP = abc_tool_app.build_application_with_arguments(
    pangebin_once_visitor.CONNECTOR,
    InitApp,
)
