"""pbfbench plASgraph2 application module."""

# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

import pbfbench.abc.tool.app as abc_tool_app
import pbfbench.topics.classification.plasgraph2.connector as plasgraphtwo_connector

APP = abc_tool_app.build_application_with_arguments(
    plasgraphtwo_connector.CONNECTOR,
    None,
)
