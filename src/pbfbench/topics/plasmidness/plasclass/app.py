"""pbfbench PlasClass application module."""

# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

import pbfbench.abc.tool.app as abc_tool_app
import pbfbench.topics.plasmidness.plasclass.visitor as plasclass_visitor

APP = abc_tool_app.build_application(plasclass_visitor.CONNECTOR)
