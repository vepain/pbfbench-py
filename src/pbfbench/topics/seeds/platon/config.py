"""Platon tool configs."""

from __future__ import annotations

from typing import final

import pbfbench.abc.tool.config as tool_cfg
import pbfbench.abc.topic.visitor as topic_visitor
import pbfbench.experiment.config as exp_cfg
import pbfbench.topics.assembly.visitor as asm_visitor


@final
class Names(tool_cfg.Names):
    """Platon names."""

    GENOME = "GENOME"

    def topic_tools(self) -> type[topic_visitor.Tools]:
        """Get topic tools."""
        match self:
            case Names.GENOME:
                return asm_visitor.Tools


@final
class Arguments(tool_cfg.Arguments[Names]):
    """Platon arguments."""

    @classmethod
    def names_type(cls) -> type[Names]:
        """Get names type."""
        return Names


Options = tool_cfg.StringOpts


@final
class Config(tool_cfg.Config[Arguments, Options]):
    """Platon tool config."""

    @classmethod
    def arguments_type(cls) -> type[Arguments]:
        """Get arguments type."""
        return Arguments

    @classmethod
    def options_type(cls) -> type[Options]:
        """Get options type."""
        return Options


@final
class ExpConfig(exp_cfg.Config[Config]):
    """Platon experiment config."""

    @classmethod
    def tool_cfg_type(cls) -> type[Config]:
        """Get tool config type."""
        return Config


if __name__ == "__main__":
    from pathlib import Path

    import typer

    p = Path("tmp_vepain/platon_exp_cfg.yaml")

    typer.echo(ExpConfig)

    exp_config = ExpConfig.from_yaml(p)

    for arg_name in Names:
        arg = exp_config.tool_configs().arguments()[arg_name]
        typer.echo(arg_name)
        typer.echo(f"* {arg.tool_name()}")
        typer.echo(f"* {arg.exp_name()}")
