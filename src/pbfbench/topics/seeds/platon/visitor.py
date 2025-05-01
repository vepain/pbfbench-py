"""Platon connector module."""

from pathlib import Path
from typing import final

import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.experiment.file_system as exp_fs
import pbfbench.topics.assembly.results.visitor as asm_res_visitor
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.seeds.platon.config as platon_cfg
import pbfbench.topics.seeds.platon.description as platon_desc
import pbfbench.topics.seeds.platon.inputs as platon_inputs
import pbfbench.topics.seeds.platon.shell as platon_sh

GENOME = abc_tool_visitor.ArgumentPath(
    platon_cfg.Names.GENOME,
    asm_visitor.Tools,
    asm_res_visitor.fasta_gz,
    platon_sh.GenomeInputLinesBuilder,
)


@final
class Connector(
    abc_tool_visitor.Connector[
        platon_cfg.Config,
        platon_inputs.Inputs,
        platon_sh.Commands,
    ],
):
    """Platon connectors."""

    @classmethod
    def config_to_inputs(
        cls,
        config: platon_cfg.Config,
        data_dir: Path,
    ) -> platon_inputs.Inputs:
        """Convert config to inputs."""
        return platon_inputs.Inputs(
            GENOME.arg_to_checkable_input(
                config.arguments(),
                data_dir,
            ),
        )

    @classmethod
    def inputs_to_commands(
        cls,
        config: platon_cfg.Config,
        inputs: platon_inputs.Inputs,
        working_exp_fs_manager: exp_fs.Manager,
    ) -> platon_sh.Commands:
        """Convert inputs to commands."""
        return platon_sh.Commands(
            GENOME.input_to_sh_lines_builder(inputs.genome()),
            config.options(),
            working_exp_fs_manager,
        )


CONNECTOR = Connector(platon_desc.DESCRIPTION)
