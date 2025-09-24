"""YAML interface module."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import yaml  # type: ignore[import-untyped]

try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper

from typing import Self


class YAMLInterface(ABC):
    """YAML interface."""

    @classmethod
    def from_yaml(cls, yaml_filepath: Path) -> Self:
        """Get object from YAML file."""
        with yaml_filepath.open("r") as file:
            obj_dict = yaml.safe_load(file)
        return cls.from_yaml_load(obj_dict)

    @classmethod
    @abstractmethod
    def from_yaml_load(cls, pyyaml_obj: yaml.YAMLObject) -> Self:
        """Convert pyyaml object to self."""
        raise NotImplementedError

    @abstractmethod
    def to_yaml_dump(self) -> yaml.YAMLObject:
        """Convert to dict."""
        raise NotImplementedError

    def to_yaml(self, yaml_filepath: Path) -> Path:
        """Write to yaml."""
        yaml_filepath = Path(yaml_filepath)
        with yaml_filepath.open("w") as file:
            yaml.dump(self.to_yaml_dump(), file, Dumper=Dumper, sort_keys=False)
        return yaml_filepath
