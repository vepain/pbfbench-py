"""PlasBin-flow result formatting module."""

import gzip

import pandas as pd
from Bio import SeqIO

import pbfbench.abc.tool.connector as abc_tool_connector
import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.items as smp_items
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.classification.platon.results as platon_res
from pbfbench.topics.classification.platon import connector

from . import results


def plasmidness(
    platon_data_exp_fs_manager: exp_fs.DataManager,
    sample_item: smp_items.Item,
) -> results.Plasmidness:
    """Convert Platon result into plasmidness PlasBin-flow input."""
    plasmidness_res = platon_res.PlasmidStats(platon_data_exp_fs_manager)
    pbf_plasmidness_res = results.Plasmidness(
        platon_data_exp_fs_manager,
    )

    platon_genome_arg = abc_tool_connector.get_arg(
        platon_data_exp_fs_manager,
        connector.GenomeArg,
    )
    if isinstance(platon_genome_arg, abc_tool_connector.InvalidToolNameError):
        _err_msg = (
            f"Invalid tool name `{platon_genome_arg.invalid_tool_name()}`"
            f" for argument name `{platon_genome_arg.arg_name()}`."
        )
        raise TypeError(_err_msg)

    asm_data_fs_manager = exp_fs.DataManager(
        platon_data_exp_fs_manager.root_dir(),
        asm_visitor.Tools(platon_genome_arg.tool()).to_description(),
        platon_genome_arg.exp_name(),
    )
    fasta_gz = (
        platon_genome_arg.result_visitor()
        .result_builder()(asm_data_fs_manager)
        .fasta_gz(sample_item.exp_sample_id())
    )

    with plasmidness_res.tsv(sample_item.exp_sample_id()).open() as tsv_file:
        set_of_platon_ids = {line.split("\t")[0] for line in tsv_file}

    with (
        pbf_plasmidness_res.tsv(sample_item.exp_sample_id()).open("w") as tsv_file,
        gzip.open(fasta_gz, "rt") as fasta_gz_file,
    ):
        for record in SeqIO.parse(fasta_gz_file, "fasta"):
            if record.name in set_of_platon_ids:
                tsv_file.write(f"{record.name}\t1\n")
            else:
                tsv_file.write(f"{record.name}\t0\n")

    return pbf_plasmidness_res


def seeds(
    platon_data_exp_fs_manager: exp_fs.DataManager,
    sample_item: smp_items.Item,
) -> results.Seeds:
    """Convert plasmid stats to PBF format."""
    seeds_res = platon_res.PlasmidStats(platon_data_exp_fs_manager)
    pbf_seeds_res = results.Seeds(
        platon_data_exp_fs_manager,
    )

    platon_seeds_stats_df = pd.read_csv(
        seeds_res.tsv(sample_item.exp_sample_id()),
        sep="\t",
    )

    platon_seeds_stats_df.to_csv(
        pbf_seeds_res.tsv(sample_item.exp_sample_id()),
        columns=["ID"],
        header=False,
        sep="\t",
        index=False,
    )
    return pbf_seeds_res
