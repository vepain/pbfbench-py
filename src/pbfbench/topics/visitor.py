"""Topic visitor."""

import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.items as topics_items
import pbfbench.topics.plasmidness.visitor as plasmidness_visitor
import pbfbench.topics.seeds.visitor as seeds_visitor


def tools(topic: topics_items.Topics) -> type[abc_topic_visitor.Tools]:
    """Visit topic tools."""
    match topic:
        case topics_items.Topics.ASSEMBLY:
            return asm_visitor.Tools
        case topics_items.Topics.SEEDS:
            return seeds_visitor.Tools
        case topics_items.Topics.PLASMIDNESS:
            return plasmidness_visitor.Tools
