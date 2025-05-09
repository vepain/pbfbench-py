"""Tool tree helping module."""


# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.markdown import Markdown as Md

import pbfbench.abc.topic.visitor as abc_topics_visitor
import pbfbench.topics.items as topics_items
import pbfbench.topics.visitor as topics_visitor
from pbfbench import root_logging

_LOGGER = logging.getLogger(__name__)


TOPICS_MODULES = [
    "assembly",
    "seeds",
]


def tool_tree(
    markdown_file: Annotated[Path | None, typer.Argument(help="Markdown file")] = None,
) -> None:
    """Tool tree command."""
    root_logging.init_logger(_LOGGER, "Running tool tree helper", False)  # noqa: FBT003
    md_string = (
        "# Tool tree\n"
        "\n"
        "Topics are at the first level, and tools are at the second level.\n"
        "The commands are under parenthesis.\n"
        "\n"
    )

    for topic in topics_items.Topics:
        topic_description = topic.to_description()
        tools: type[abc_topics_visitor.Tools] = topics_visitor.tools(topic)
        md_string += f"* {topic_description.name()} ({topic_description.cmd()})\n"
        for tool in tools:
            tool_description = tool.to_description()
            md_string += f"  * {tool_description.name()} ({tool_description.cmd()})\n"

    root_logging.CONSOLE.print(Md(md_string))

    if markdown_file is not None:
        _LOGGER.info("Saving markdown file to `%s`", markdown_file)
        with markdown_file.open("w") as f_out:
            f_out.write(md_string)
