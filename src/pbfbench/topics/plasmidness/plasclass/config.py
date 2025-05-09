"""PlasClass tool configs."""

from __future__ import annotations

from typing import final

import pbfbench.abc.tool.config as abc_tool_cfg
import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.experiment.config as exp_cfg
import pbfbench.topics.assembly.visitor as asm_visitor


@final
class Names(abc_tool_cfg.Names):
    """PlasClass argument names."""

    FASTA = "FASTA"

    def topic_tools(self) -> type[abc_topic_visitor.Tools]:
        """Get topic tools."""
        match self:
            case Names.FASTA:
                return asm_visitor.Tools


@final
class Arguments(abc_tool_cfg.Arguments[Names]):
    """PlasClass arguments."""

    @classmethod
    def names_type(cls) -> type[Names]:
        """Get names type."""
        return Names


@final
class Config(abc_tool_cfg.Config[Names]):
    """PlasClass config."""

    @classmethod
    def arguments_type(cls) -> type[Arguments]:
        """Get arguments type."""
        return Arguments


@final
class ExpConfig(exp_cfg.Config[Names]):
    """PlasClass experiment config."""

    @classmethod
    def tool_cfg_type(cls) -> type[Config]:
        """Get tool config type."""
        return Config
