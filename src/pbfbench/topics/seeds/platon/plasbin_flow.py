"""PlasBin-flow result formatting module."""

import pandas as pd

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.items as smp_items
import pbfbench.topics.seeds.pbf_input.results as plm_pbf_in_res
import pbfbench.topics.seeds.platon.results as platon_res


def convert(
    input_data_exp_fs_manager: exp_fs.DataManager,
    sample_item: smp_items.Item,
    requesting_tool_desc: abc_tool_desc.Description,
) -> None:
    """Convert plasmid stats to PBF format."""
    seeds_res = platon_res.PlasmidStats(input_data_exp_fs_manager)
    pbf_seeds_res = plm_pbf_in_res.Seeds(
        input_data_exp_fs_manager,
        requesting_tool_desc,
    )

    platon_seeds_stats_df = pd.read_csv(
        seeds_res.tsv(sample_item.exp_sample_id()),
        sep="\t",
    )

    platon_seeds_stats_df.to_csv(
        pbf_seeds_res.tsv(sample_item.exp_sample_id()),
        columns=["ID"],
        sep="\t",
        index=True,
    )
