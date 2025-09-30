"""Platon connector module."""

from __future__ import annotations

from typing import final

import pbfbench.abc.tool.connector as abc_tool_connector
import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.abc.topic.visitor as abc_topic_visitor
import pbfbench.topics.assembly.results as asm_res
import pbfbench.topics.assembly.visitor as asm_visitor

from . import description as desc
from . import shell as sh


@final
class Names(abc_tool_connector.Names):
    """Platon names."""

    GENOME = "GENOME"

    def topic_tools(self) -> type[abc_topic_visitor.Tools]:
        """Get topic tools."""
        match self:
            case Names.GENOME:
                return asm_visitor.Tools


@final
class GenomeArg(abc_tool_connector.Arg[Names, asm_visitor.Tools, asm_res.FastaGZ]):
    """Genome argument."""

    @classmethod
    def name(cls) -> Names:
        """Get name."""
        return Names.GENOME

    @classmethod
    def tools_type(cls) -> type[asm_visitor.Tools]:
        """Get tools type."""
        return asm_visitor.Tools

    @classmethod
    def result_visitor(cls) -> type[asm_res.FastaGZVisitor]:
        """Get result visitor."""
        return asm_res.FastaGZVisitor

    @classmethod
    def sh_lines_builder_type(cls) -> type[sh.GenomeInputLinesBuilder]:
        """Get shell lines builder type."""
        return sh.GenomeInputLinesBuilder


@final
class Arguments(abc_tool_connector.Arguments[Names]):
    """Platon arguments."""

    @classmethod
    def names_type(cls) -> type[Names]:
        """Get names type."""
        return Names

    @classmethod
    def arg_types(cls) -> list[type[abc_tool_connector.Arg]]:
        """Get list of arg types."""
        return [
            GenomeArg,
        ]


@final
class Connector(abc_tool_connector.WithArguments[Names]):
    """Platon connector."""

    @classmethod
    def description(cls) -> abc_tool_desc.Description:
        """Get description."""
        return desc.DESCRIPTION

    @classmethod
    def arguments_type(cls) -> type[Arguments]:
        """Get arguments type."""
        return Arguments
