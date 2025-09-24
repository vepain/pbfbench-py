"""Topic application module."""

# Due to typer usage:

from __future__ import annotations

import pbfbench.abc.topic.app as abc_topic_app

from . import description as desc
from .pangebin_once import app as pangebin_once_app

APP = abc_topic_app.build_application(
    desc.DESCRIPTION,
    [pangebin_once_app.APP],
)
