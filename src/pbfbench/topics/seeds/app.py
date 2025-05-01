"""Seeds topic application module."""

# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

import pbfbench.abc.topic.app as abc_topic_app
import pbfbench.topics.seeds.description as seeds_desc
import pbfbench.topics.seeds.platon.app as platon_app

APP = abc_topic_app.build_application(seeds_desc.DESCRIPTION, [platon_app.APP])
