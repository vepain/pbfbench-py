"""ABC topic result visitors."""

from abc import ABC, abstractmethod

import pbfbench.abc.topic.results.items as abc_topic_res_items
import pbfbench.abc.topic.visitor as abc_topic_visitor


class Visitor[T: abc_topic_visitor.Tools, R: abc_topic_res_items.Result](ABC):
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


class Original[
    T: abc_topic_visitor.Tools,
    OriginalResult: abc_topic_res_items.Original,
](Visitor[T, OriginalResult]):
    """Original result visitor."""


class Formatted[
    T: abc_topic_visitor.Tools,
    FormattedResult: abc_topic_res_items.Formatted,
](
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
