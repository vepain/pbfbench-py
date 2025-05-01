"""Platon tool configs."""

from __future__ import annotations

from typing import final

import pbfbench.abc.tool.config as tool_cfg
import pbfbench.experiment.config as exp_cfg


@final
class Names(tool_cfg.Names):
    """Platon names."""

    GENOME = "GENOME"


@final
class Arguments(tool_cfg.Arguments[Names]):
    """Platon arguments."""


Options = tool_cfg.StringOpts


@final
class Config(tool_cfg.Config[Arguments, Options]):
    """Platon tool config."""


@final
class ExpConfig(exp_cfg.Config[Config]):
    """Platon experiment config."""


if __name__ == "__main__":
    from pathlib import Path

    p = Path("tmp_vepain/platon_exp_cfg.yaml")

    exp_config = ExpConfig.from_yaml(p)

    for arg_name in Names:
        arg = exp_config.tool_configs().arguments()[arg_name]
        print(arg_name)
        print(f"* {arg.tool_name()}")
        print(f"* {arg.exp_name()}")
