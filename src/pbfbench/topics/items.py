"""Topics module."""

from typing import final

import pbfbench.abc.topic.description as abc_topic_desc
import pbfbench.abc.topic.visitor as abc_topic_visitor

from .assembly import description as asm_desc
from .classification import description as class_desc


@final
class Topics(abc_topic_visitor.Topics):
    """Topic names."""

    ASSEMBLY = asm_desc.DESCRIPTION.name()
    CLASSIFICATION = class_desc.DESCRIPTION.name()

    def to_description(self) -> abc_topic_desc.Description:
        """Get topic description."""
        match self:
            case Topics.ASSEMBLY:
                return asm_desc.DESCRIPTION
            case Topics.CLASSIFICATION:
                return class_desc.DESCRIPTION
