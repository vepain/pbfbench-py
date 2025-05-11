"""Plasmidness topic application module."""

# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

import pbfbench.abc.topic.app as abc_topic_app
import pbfbench.topics.plasmidness.description as plasmidness_desc
import pbfbench.topics.plasmidness.plasclass.app as plasclass_app
import pbfbench.topics.plasmidness.plasgraphtwo.app as plasgraphtwo_app

APP = abc_topic_app.build_application(
    plasmidness_desc.DESCRIPTION,
    [plasclass_app.APP, plasgraphtwo_app.APP],
)
