"""Concrete tool application module."""

from __future__ import annotations

import pbfbench.abc.tool.app as abc_tool_app
import pbfbench.topics.binning.pangebin_once.connector as pangebin_once_visitor

APP = abc_tool_app.build_application(
    pangebin_once_visitor.CONNECTOR,
    InitApp,
)
