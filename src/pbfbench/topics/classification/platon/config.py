"""Platon tool configs."""

from __future__ import annotations

from typing import final

import pbfbench.abc.tool.config as abc_tool_cfg
import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.experiment.config as exp_cfg
import pbfbench.topics.assembly.visitor as asm_visitor


@final
class Names(abc_tool_cfg.Names):
    """Platon names."""

    GENOME = "GENOME"

    def topic_tools(self) -> type[abc_topic_visitor.Tools]:
        """Get topic tools."""
        match self:
            case Names.GENOME:
                return asm_visitor.Tools


@final
class Arguments(abc_tool_cfg.Arguments[Names]):
    """Platon arguments."""

    @classmethod
    def names_type(cls) -> type[Names]:
        """Get names type."""
        return Names


@final
class Config(abc_tool_cfg.ConfigWithArguments[Names]):
    """Platon config."""

    @classmethod
    def arguments_type(cls) -> type[Arguments]:
        """Get arguments type."""
        return Arguments


@final
class ExpConfig(exp_cfg.ConfigWithArguments[Config]):
    """Platon experiment config."""

    @classmethod
    def tool_cfg_type(cls) -> type[Config]:
        """Get tool config type."""
        return Config
