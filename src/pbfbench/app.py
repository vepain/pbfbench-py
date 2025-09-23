"""Root pbfbench application module."""

# Due to typer usage:

from __future__ import annotations

from enum import StrEnum

import typer

import pbfbench.doc.app as doc_app
import pbfbench.help.app as help_app
import pbfbench.topics.assembly.app as assembly_app

# import pbfbench.topics.binning.app as binning_app
import pbfbench.topics.classification.app as class_app


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
for app in (
    assembly_app.APP,
    class_app.APP,
    # binning_app.APP
):
    APP.add_typer(app, rich_help_panel=CommandCategories.TOPICS)
