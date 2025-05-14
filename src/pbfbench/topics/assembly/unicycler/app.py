"""Concrete tool application module."""

# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

import pbfbench.abc.tool.app as abc_tool_app
import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.topics.assembly.unicycler.description as unicycler_desc

APP = abc_tool_app.build_application_only_options(
    abc_tool_visitor.ConnectorOnlyOptions(unicycler_desc.DESCRIPTION),
)
