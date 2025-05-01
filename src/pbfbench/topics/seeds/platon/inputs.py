"""Platon input checks."""

from __future__ import annotations

from typing import final

import pbfbench.abc.tool.inputs as abc_tool_inputs
import pbfbench.abc.topic.results.items as abc_topic_results
import pbfbench.topics.assembly.results.items as asm_results
import pbfbench.topics.seeds.platon.config as platon_cfg


@final
class Inputs(abc_tool_inputs.Inputs[platon_cfg.Names]):
    """Platon inputs."""

    def __init__(self, genome_input: asm_results.FastaGZ) -> None:
        """Initialize."""
        self.__genome_input = genome_input

    def genome(self) -> asm_results.FastaGZ:
        """Get genome input."""
        return self.__genome_input

    def _name_to_input(self, arg_name: platon_cfg.Names) -> abc_topic_results.Result:
        """Get input."""
        # REFACTOR move up (tool visitor mod)?
        match arg_name:
            case platon_cfg.Names.GENOME:
                return self.__genome_input
