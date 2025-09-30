"""Topic visitor."""

import pbfbench.abc.topic.visitor as abc_topic_visitor

from . import items as topics_items
from .assembly import visitor as asm_visitor
from .classification import visitor as class_visitor


def tools(topic: topics_items.Topics) -> type[abc_topic_visitor.Tools]:
    """Visit topic tools."""
    match topic:
        case topics_items.Topics.ASSEMBLY:
            return asm_visitor.Tools
        case topics_items.Topics.CLASSIFICATION:
            return class_visitor.Tools
