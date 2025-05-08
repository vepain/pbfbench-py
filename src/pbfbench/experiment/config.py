"""Experiment configuration.

Wrapper for exp_cfg.yaml files.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Self

import pbfbench.abc.tool.config as abc_tool_cfg
import pbfbench.slurm.config as slurm_cfg
from pbfbench.yaml_interface import YAMLInterface


class Config[N: abc_tool_cfg.Names](YAMLInterface, ABC):
    """Experiment wrapper."""

    KEY_NAME = "name"
    KEY_TOOL = "tool"
    KEY_SLURM = "slurm"

    @classmethod
    @abstractmethod
    def tool_cfg_type(cls) -> type[abc_tool_cfg.Config[N]]:
        """Get tool config type."""
        raise NotImplementedError

    @classmethod
    def from_yaml_load(cls, obj_dict: dict[str, Any]) -> Self:
        """Convert dict to object."""
        return cls(
            obj_dict[cls.KEY_NAME],
            cls.tool_cfg_type().from_yaml_load(obj_dict[cls.KEY_TOOL]),
            slurm_cfg.Config.from_yaml_load(obj_dict[cls.KEY_SLURM]),
        )

    def __init__(
        self,
        name: str,
        tool_configs: abc_tool_cfg.Config[N],
        slurm_config: slurm_cfg.Config,
    ) -> None:
        self.__name = name
        self.__tool_configs = tool_configs
        self.__slurm_config = slurm_config

    def name(self) -> str:
        """Get name."""
        return self.__name

    def tool_configs(self) -> abc_tool_cfg.Config[N]:
        """Get tool configs."""
        return self.__tool_configs

    def slurm_config(self) -> slurm_cfg.Config:
        """Get slurm config."""
        return self.__slurm_config

    def is_same(self, other: Self) -> bool:
        """Check if experiment is the same."""
        return self.to_yaml_dump() == other.to_yaml_dump()

    def to_yaml_dump(self) -> dict[str, Any]:
        """Convert to dict."""
        return {
            self.KEY_NAME: self.__name,
            self.KEY_TOOL: self.__tool_configs.to_yaml_dump(),
            self.KEY_SLURM: self.__slurm_config.to_yaml_dump(),
        }
