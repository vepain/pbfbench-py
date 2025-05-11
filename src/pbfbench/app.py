"""Root pbfbench application module."""

# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

from enum import StrEnum

import typer

import pbfbench.doc.app as doc_app
import pbfbench.help.app as help_app
import pbfbench.topics.plasmidness.app as plasmidness_app
import pbfbench.topics.seeds.app as seeds_app


class PBFCommand:
    """PBF command."""

    NAME = "pbfbench"
    HELP = "PlasBin-flow benchmarking framework"


APP = typer.Typer(
    name=PBFCommand.NAME,
    help=PBFCommand.HELP,
    rich_markup_mode="rich",
)


class CommandCategories(StrEnum):
    """Command categories."""

    UTILITIES = "Utilities"
    TOPICS = "Topics"


#
# Utilities
#
for app in (doc_app.APP, help_app.APP):
    APP.add_typer(app, rich_help_panel=CommandCategories.UTILITIES)

#
# Topics
#
for app in (seeds_app.APP, plasmidness_app.APP):
    APP.add_typer(app, rich_help_panel=CommandCategories.TOPICS)
