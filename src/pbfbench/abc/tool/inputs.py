"""Tools checking abstract module."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, get_args

import pbfbench.abc.tool.config as abc_tool_config
import pbfbench.abc.topic.results.items as abc_topic_results
import pbfbench.abc.topic.results.items as topic_result

if TYPE_CHECKING:
    from collections.abc import Iterator


class Inputs[N: abc_tool_config.Names](ABC):
    """Inputs container."""

    @classmethod
    def names_type(cls) -> type[N]:
        """Get names type."""
        return get_args(cls)[0]

    def names_with_inputs(
        self,
    ) -> Iterator[tuple[N, abc_topic_results.Result]]:
        """Get names with inputs."""
        for name in self.names_type():
            yield name, self._name_to_input(name)

    @abstractmethod
    def _name_to_input(self, arg_name: N) -> topic_result.Result:
        """Get input."""
        raise NotImplementedError
