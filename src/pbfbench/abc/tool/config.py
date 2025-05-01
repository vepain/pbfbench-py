"""Tool config module."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Self

from pbfbench.yaml_interface import YAMLInterface

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    import pbfbench.abc.topic.visitor as topic_visitor


class Names(StrEnum):
    """Tool names."""

    @abstractmethod
    def topic_tools(self) -> type[topic_visitor.Tools]:
        """Get topic tools."""
        raise NotImplementedError


class Arguments[N: Names](YAMLInterface, ABC):
    """Tool arguments configuration."""

    @classmethod
    @abstractmethod
    def names_type(cls) -> type[N]:
        """Get names type."""
        raise NotImplementedError

    @classmethod
    def from_yaml_load(cls, pyyaml_obj: dict[str, list[str]]) -> Self:
        """Convert dict to object."""
        return cls(
            {
                cls.names_type()(name): Arg.from_yaml_load(yaml_data)
                for name, yaml_data in pyyaml_obj.items()
            },
        )

    def __init__(self, arguments: dict[N, Arg]) -> None:
        self.__arguments = arguments

    def __getitem__(self, name: N) -> Arg:
        """Get argument."""
        return self.__arguments[name]

    def to_yaml_dump(self) -> dict[str, Any]:
        """Convert to dict."""
        return {str(name): arg.to_yaml_dump() for name, arg in self.__arguments.items()}


class Arg(YAMLInterface):
    """Tool argument configuration."""

    @classmethod
    def from_yaml_load(cls, yaml_data: list[str]) -> Self:
        """Convert dict to object."""
        tool_name, exp_name = yaml_data
        return cls(tool_name, exp_name)

    def __init__(self, tool_name: str, exp_name: str) -> None:
        """Initialize."""
        self.__tool_name = tool_name
        self.__exp_name = exp_name

    def tool_name(self) -> str:
        """Get tool name."""
        return self.__tool_name

    def exp_name(self) -> str:
        """Get experiment name."""
        return self.__exp_name

    def to_yaml_dump(self) -> list[str]:
        """Convert to yaml dump."""
        return [self.__tool_name, self.__exp_name]


class StringOpts(YAMLInterface):
    """String options.

    When the options are regular short/long options.
    """

    @classmethod
    def from_yaml_load(cls, obj_list: list[str]) -> Self:
        """Convert dict to object."""
        return cls(obj_list)

    def __init__(self, options: Iterable[str]) -> None:
        self.__options = list(options)

    def __iter__(self) -> Iterator[str]:
        """Iterate options."""
        return iter(self.__options)

    def to_yaml_dump(self) -> list[str]:
        """Convert to dict."""
        return self.__options


Options = YAMLInterface


class Config[Args: Arguments, Opts: Options](YAMLInterface):
    """Tool config module."""

    KEY_ARGUMENTS = "arguments"
    KEY_OPTIONS = "options"

    @classmethod
    @abstractmethod
    def arguments_type(cls) -> type[Args]:
        """Get argument arguments type."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def options_type(cls) -> type[Opts]:
        """Get options type."""
        raise NotImplementedError

    @classmethod
    def from_yaml_load(cls, obj_dict: dict[str, Any]) -> Self:
        """Convert dict to object."""
        return cls(
            cls.arguments_type().from_yaml_load(obj_dict[cls.KEY_ARGUMENTS]),
            cls.options_type().from_yaml_load(obj_dict[cls.KEY_OPTIONS]),
        )

    def __init__(self, arguments: Args, options: Opts) -> None:
        """Initialize."""
        self.__arguments = arguments
        self.__options = options

    def arguments(self) -> Args:
        """Get arguments."""
        return self.__arguments

    def options(self) -> Opts:
        """Get options."""
        return self.__options

    def to_yaml_dump(self) -> dict[str, Any]:
        """Convert to dict."""
        return {
            self.KEY_ARGUMENTS: self.__arguments.to_yaml_dump(),
            self.KEY_OPTIONS: self.__options.to_yaml_dump(),
        }
