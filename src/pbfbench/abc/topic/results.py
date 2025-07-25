"""Abstract tools results items module."""

from abc import ABC, abstractmethod

import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.items as smp_items
import pbfbench.samples.status as smp_status


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
    def result_builder_from_tool(cls, tool: T) -> type[R]:
        """Get result builder."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def result_builder(cls) -> type[R]:
        """Get result builder."""
        raise NotImplementedError


class OriginalVisitor[T: abc_topic_visitor.Tools, OriginalResult: Original](
    Visitor[T, OriginalResult],
):
    """Original result visitor."""


class FormattedVisitor[T: abc_topic_visitor.Tools, FormattedResult: Formatted](
    Visitor[T, FormattedResult],
):
    """Formatted result visitor."""

    @classmethod
    def result_builder_from_tool(
        cls,
        _: T,
    ) -> type[FormattedResult]:
        """Get result builder."""
        return cls.result_builder()
