"""Topics module."""

import importlib
from enum import StrEnum

import pbfbench.abc.topic.description as abc_topic_desc
import pbfbench.topics.assembly.description as assembly_desc
import pbfbench.topics.seeds.description as seeds_desc


class Names(StrEnum):
    """Topic names."""

    ASSEMBLY = assembly_desc.DESCRIPTION.name()
    SEEDS = seeds_desc.DESCRIPTION.name()

    def to_description(self) -> abc_topic_desc.Description:
        """Get topic description."""
        return importlib.import_module(
            f"pbfbench.topics.{self.lower()}.description",
        ).DESCRIPTION
