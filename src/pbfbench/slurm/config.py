"""Slurm configs."""

from __future__ import annotations

from typing import Self

from pbfbench.yaml_interface import YAMLInterface


class Config(list[str], YAMLInterface):
    """Slurm config."""

    @classmethod
    def from_yaml_load(cls, pyyaml_obj: list[str]) -> Self:
        """Convert pyyaml object to self."""
        return cls(iter(pyyaml_obj))

    def to_yaml_dump(self) -> list[str]:
        """Convert to list."""
        return list(self)
