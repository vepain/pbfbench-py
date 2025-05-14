"""Topic application module."""

# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

import pbfbench.abc.topic.app as abc_topic_app
import pbfbench.topics.binning.description as topic_desc
import pbfbench.topics.binning.pangebin_once.app as pangebin_once_app

APP = abc_topic_app.build_application(
    topic_desc.DESCRIPTION,
    [pangebin_once_app.APP],
)
