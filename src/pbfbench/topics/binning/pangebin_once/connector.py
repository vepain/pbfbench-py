"""Concrete tool connector module."""

from __future__ import annotations

from typing import final

import pbfbench.abc.tool.connector as abc_tool_connector
import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.topics.assembly.results as asm_res
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.classification.visitor as class_visitor
from pbfbench.topics.binning.plasbin_flow.format.classification import (
    results as fmt_class_res,
)
from pbfbench.topics.binning.plasbin_flow.format.classification import (
    visitor as fmt_class_visitor,
)

from . import description as desc
from . import shell as sh


@final
class Names(abc_tool_connector.Names):
    """Argument names."""

    GFA = "GFA"
    SEEDS = "SEEDS"
    PLASMIDNESS = "PLASMIDNESS"

    def topic_tools(self) -> type[abc_topic_visitor.Tools]:
        """Get topic tools."""
        match self:
            case Names.GFA:
                return asm_visitor.Tools
            case Names.SEEDS:
                return class_visitor.Tools
            case Names.PLASMIDNESS:
                return class_visitor.Tools


@final
class GFAArg(abc_tool_connector.Arg[Names, asm_visitor.Tools, asm_res.AsmGraphGZ]):
    """GFA argument."""

    @classmethod
    def name(cls) -> Names:
        """Get name."""
        return Names.GFA

    @classmethod
    def tools_type(cls) -> type[asm_visitor.Tools]:
        """Get tools type."""
        return asm_visitor.Tools

    @classmethod
    def result_visitor(cls) -> type[asm_res.AsmGraphGZVisitor]:
        """Get result visitor."""
        return asm_res.AsmGraphGZVisitor

    @classmethod
    def sh_lines_builder_type(cls) -> type[sh.GFAInputLinesBuilder]:
        """Get shell lines builder type."""
        return sh.GFAInputLinesBuilder


@final
class SeedsArg(
    abc_tool_connector.Arg[Names, class_visitor.Tools, fmt_class_res.Seeds],
):
    """Seeds argument."""

    @classmethod
    def name(cls) -> Names:
        """Get name."""
        return Names.SEEDS

    @classmethod
    def tools_type(cls) -> type[class_visitor.Tools]:
        """Get tools type."""
        return class_visitor.Tools

    @classmethod
    def result_visitor(cls) -> type[fmt_class_visitor.SeedsVisitor]:
        """Get result visitor."""
        return fmt_class_visitor.SeedsVisitor

    @classmethod
    def sh_lines_builder_type(cls) -> type[sh.SeedsInputLinesBuilder]:
        """Get shell lines builder type."""
        return sh.SeedsInputLinesBuilder


@final
class PlasmidnessArg(
    abc_tool_connector.Arg[Names, class_visitor.Tools, fmt_class_res.Plasmidness],
):
    """Plasmidness argument."""

    @classmethod
    def name(cls) -> Names:
        """Get name."""
        return Names.PLASMIDNESS

    @classmethod
    def tools_type(cls) -> type[class_visitor.Tools]:
        """Get tools type."""
        return class_visitor.Tools

    @classmethod
    def result_visitor(cls) -> type[fmt_class_visitor.PlasmidnessVisitor]:
        """Get result visitor."""
        return fmt_class_visitor.PlasmidnessVisitor

    @classmethod
    def sh_lines_builder_type(
        cls,
    ) -> type[sh.PlasmidnessInputLinesBuilder]:
        """Get shell lines builder type."""
        return sh.PlasmidnessInputLinesBuilder


@final
class Arguments(abc_tool_connector.Arguments[Names]):
    """Concrete tool arguments."""

    @classmethod
    def names_type(cls) -> type[Names]:
        """Get names type."""
        return Names

    @classmethod
    def arg_types(cls) -> list[type[abc_tool_connector.Arg]]:
        """Get list of arg types."""
        return [
            GFAArg,
            SeedsArg,
            PlasmidnessArg,
        ]


@final
class Connector(abc_tool_connector.WithArguments[Names]):
    """Concrete tool connector."""

    @classmethod
    def description(cls) -> abc_tool_desc.Description:
        """Get description."""
        return desc.DESCRIPTION

    @classmethod
    def arguments_type(cls) -> type[Arguments]:
        """Get arguments type."""
        return Arguments
