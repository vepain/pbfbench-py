"""pbfbench Platon application module."""

# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

import pbfbench.abc.tool.app as abc_tool_app
import pbfbench.topics.seeds.platon.visitor as platon_visitor

APP = abc_tool_app.build_application_with_arguments(platon_visitor.CONNECTOR)
