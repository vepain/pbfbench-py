"""Concrete tool application module."""

from __future__ import annotations

import pbfbench.abc.tool.app as abc_tool_app

from . import connector

APP = abc_tool_app.build_application(connector.Connector)
