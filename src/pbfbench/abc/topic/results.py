"""Abstract tools results items module."""

from abc import ABC, abstractmethod
from collections.abc import Callable

import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.items as smp_items
import pbfbench.samples.status as smp_status


class Error:
    """Error to get the result."""

    def __init__(self, msg: str) -> None:
        """Initialize."""
        self.__msg = msg

    def __str__(self) -> str:
        """Get the error message."""
        return self.__msg


class Result(ABC):
    """Result base."""

    def __init__(self, exp_fs_manager: exp_fs.ManagerBase) -> None:
        """Initialize."""
        self._exp_fs_manager = exp_fs_manager

    def exp_fs_manager(self) -> exp_fs.ManagerBase:
        """Get file system manager."""
        return self._exp_fs_manager

    # REFACTOR not sure it is relevant to use sample status, because of formatted
    @abstractmethod
    def check(self, sample_item: smp_items.Item) -> smp_status.Status:
        """Check input(s)."""
        raise NotImplementedError


class Original(Result):
    """Original result."""

    def check(self, sample_item: smp_items.Item) -> smp_status.Status:
        """Check input(s)."""
        return smp_status.get_status(
            self._exp_fs_manager.sample_fs_manager(sample_item),
        )


class Formatted(Result):
    """Formatted result."""


# Separate the visitor from the result class
# because some result are really specific, other are conventionnal.
# Only conventionnal results have a visitor.
class Visitor[T: abc_topic_visitor.Tools, R: Result](ABC):
    """Abstract result visitor."""

    @classmethod
    @abstractmethod
    def result_builder(cls) -> type[R]:
        """Get result builder."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def result_builder_from_tool(cls, tool: T) -> Error | type[R]:
        """Get result builder."""
        raise NotImplementedError

    @classmethod
    def tool_gives_the_result(cls, tool: T) -> bool:
        """Check if the tool gives the result."""
        return cls.result_builder_from_tool(tool) is not Error


class OriginalVisitor[T: abc_topic_visitor.Tools, OriginalResult: Original](
    Visitor[T, OriginalResult],
):
    """Original result visitor."""


type ConvertFn[FormattedResult: Formatted] = Callable[
    [exp_fs.DataManager, smp_items.Item],
    FormattedResult,
]


class FormattedVisitor[T: abc_topic_visitor.Tools, FormattedResult: Formatted](
    Visitor[T, FormattedResult],
):
    """Formatted result visitor."""

    @classmethod
    @abstractmethod
    def convert_fn(
        cls,
        tool: T,
    ) -> Error | ConvertFn[FormattedResult]:
        """Get convert function."""
        raise NotImplementedError

    @classmethod
    def result_builder_from_tool(
        cls,
        tool: T,
    ) -> Error | type[FormattedResult]:
        """Get result builder."""
        match convert_fn_or_err := cls.convert_fn(tool):
            case Error():
                return convert_fn_or_err
            case _:
                return cls.result_builder()
