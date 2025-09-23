"""pbfbench Platon application module."""

# Due to typer usage:

from __future__ import annotations

import pbfbench.abc.tool.app as abc_tool_app
import pbfbench.topics.classification.platon.connector as platon_connector

APP = abc_tool_app.build_application_with_arguments(platon_connector.Connector)
