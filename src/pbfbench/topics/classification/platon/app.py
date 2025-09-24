"""pbfbench Platon application module."""

# Due to typer usage:

from __future__ import annotations

import pbfbench.abc.tool.app as abc_tool_app

from . import connector

APP = abc_tool_app.build_application_with_arguments(connector.Connector)
