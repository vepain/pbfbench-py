"""Topic visitor."""

import importlib

import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.topics.items as topics_items


def tools(topic: topics_items.Names) -> type[abc_topic_visitor.Tools]:
    """Visit topic tools."""
    return importlib.import_module(
        f"pbfbench.topics.{topic.lower()}.visitor",
    ).Tools
