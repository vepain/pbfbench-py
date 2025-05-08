"""Topics module."""

from typing import final

import pbfbench.abc.topic.description as abc_topic_desc
import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.topics.assembly.description as asm_desc
import pbfbench.topics.seeds.description as seeds_desc

# REFACTOR reverse the sense: topic container.???
# * avoid module path hack


@final
class Topics(abc_topic_visitor.Topics):
    """Topic names."""

    ASSEMBLY = asm_desc.DESCRIPTION.name()
    SEEDS = seeds_desc.DESCRIPTION.name()

    def to_description(self) -> abc_topic_desc.Description:
        """Get topic description."""
        match self:
            case Topics.ASSEMBLY:
                return asm_desc.DESCRIPTION
            case Topics.SEEDS:
                return seeds_desc.DESCRIPTION
