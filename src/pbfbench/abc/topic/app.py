"""Topic abstract application module."""

# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

from collections.abc import Iterable

import typer

import pbfbench.abc.topic.description as abc_topic_desc


def build_application(
    topic_description: abc_topic_desc.Description,
    tool_apps: Iterable[typer.Typer],
) -> typer.Typer:
    """Build topic application."""
    app = typer.Typer(
        name=topic_description.cmd(),
        help=f"Subcommand for topic `{topic_description.name()}`",
        rich_markup_mode="rich",
    )
    for tool_app in tool_apps:
        app.add_typer(tool_app)
    return app
