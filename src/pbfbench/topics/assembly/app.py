"""Concrete topic application module."""

# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

import pbfbench.abc.topic.app as abc_topic_app
import pbfbench.topics.assembly.description as assembly_desc
import pbfbench.topics.assembly.unicycler.app as unicycler_app

APP = abc_topic_app.build_application(assembly_desc.DESCRIPTION, [unicycler_app.APP])
