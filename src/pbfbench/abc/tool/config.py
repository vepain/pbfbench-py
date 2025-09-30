"""Tool config YAML interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from pbfbench.yaml_interface import YAMLInterface

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    import yaml  # type: ignore[import-untyped]

from abc import ABC


@final
class Arg(YAMLInterface):
    """Tool config argument."""

    @classmethod
    def from_yaml_load(cls, pyyaml_obj: list[str]) -> Self:
        """Convert dict to object."""
        return cls(*pyyaml_obj)

    def __init__(self, tool_name: str, exp_name: str) -> None:
        self._tool_name = tool_name
        self._exp_name = exp_name

    def tool_name(self) -> str:
        """Get tool name."""
        return self._tool_name

    def exp_name(self) -> str:
        """Get experiment name."""
        return self._exp_name

    def to_yaml_dump(self) -> list[str]:
        """Convert to yaml dump."""
        return [self._tool_name, self._exp_name]


@final
class Arguments(YAMLInterface):
    """Tool config arguments."""

    @classmethod
    def from_yaml_load(cls, pyyaml_obj: dict[str, list[str]]) -> Self:
        """Convert dict to object."""
        return cls({name: Arg.from_yaml_load(arg) for name, arg in pyyaml_obj.items()})

    def __init__(self, arguments: dict[str, Arg]) -> None:
        self._arguments = arguments

    def arguments(self) -> dict[str, Arg]:
        """Get arguments."""
        return self._arguments

    def __getitem__(self, name: str) -> Arg:
        """Get argument."""
        return self._arguments[name]

    def to_yaml_dump(self) -> dict[str, list[str]]:
        """Convert to yaml dump."""
        return {name: arg.to_yaml_dump() for name, arg in self._arguments.items()}


@final
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

    def __bool__(self) -> bool:
        """Check if options are not empty."""
        return len(self.__options) > 0

    def __len__(self) -> int:
        """Get options length."""
        return len(self.__options)

    def __iter__(self) -> Iterator[str]:
        """Iterate options."""
        return iter(self.__options)

    def to_yaml_dump(self) -> list[str]:
        """Convert to dict."""
        return self.__options


class WithOptions(YAMLInterface, ABC):
    """Tool config with options."""

    KEY_OPTIONS = "options"

    @classmethod
    def _get_options_from_yaml_load(
        cls,
        yaml_obj: dict[str, yaml.YAMLObject],
    ) -> StringOpts:
        return StringOpts.from_yaml_load(yaml_obj.get(cls.KEY_OPTIONS, []))

    def __init__(self, options: StringOpts) -> None:
        self._options = options

    def options(self) -> StringOpts:
        """Get options."""
        return self._options

    def _options_to_yaml_dump(self) -> dict[str, list[str]]:
        if not self._options:
            return {}
        return {self.KEY_OPTIONS: self._options.to_yaml_dump()}

    def is_same(self, other: Self) -> bool:
        """Check if configs are the same."""
        return self.to_yaml_dump() == other.to_yaml_dump()


@final
class OnlyOptions(WithOptions):
    """Tool config without arguments."""

    @classmethod
    def from_yaml_load(cls, obj_dict: dict[str, yaml.YAMLObject]) -> Self:
        """Convert dict to object."""
        return cls(cls._get_options_from_yaml_load(obj_dict))

    def to_yaml_dump(self) -> dict[str, yaml.YAMLObject]:
        """Convert to dict."""
        return self._options_to_yaml_dump()


@final
class WithArguments(WithOptions):
    """Tool config with arguments."""

    KEY_ARGUMENTS = "arguments"

    @classmethod
    def from_yaml_load(cls, obj_dict: dict[str, yaml.YAMLObject]) -> Self:
        """Convert dict to object."""
        return cls(
            Arguments.from_yaml_load(obj_dict[cls.KEY_ARGUMENTS]),
            cls._get_options_from_yaml_load(obj_dict),
        )

    def __init__(self, arguments: Arguments, options: StringOpts) -> None:
        """Initialize."""
        super().__init__(options)
        self.__arguments = arguments

    def arguments(self) -> Arguments:
        """Get arguments."""
        return self.__arguments

    def to_yaml_dump(self) -> dict[str, yaml.YAMLObject]:
        """Convert to dict."""
        return {
            self.KEY_ARGUMENTS: self.__arguments.to_yaml_dump(),
            **self._options_to_yaml_dump(),
        }
