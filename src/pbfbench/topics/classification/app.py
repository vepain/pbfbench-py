"""Classification topic application module."""

# Due to typer usage:

from __future__ import annotations

import pbfbench.abc.topic.app as abc_topic_app

from . import description as class_desc

# from .plasclass import app as plasclass_app
# from .plasgraph2 import app as plasgraphtwo_app
from .platon import app as platon_app

APP = abc_topic_app.build_application(
    class_desc.DESCRIPTION,
    [
        # plasclass_app.APP, plasgraphtwo_app.APP,
        platon_app.APP,
    ],
)
