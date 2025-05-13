"""PlasBin-flow result formatting module."""

import pandas as pd

import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.items as smp_items
import pbfbench.topics.assembly.results.items as asm_res_items
import pbfbench.topics.assembly.visitor as asm_visitor
import pbfbench.topics.plasmidness.pbf_input.ops as plm_pbf_in_ops
import pbfbench.topics.plasmidness.pbf_input.results as plm_pbf_in_res
import pbfbench.topics.plasmidness.plasgraph2.config as plasgraph2_cfg
import pbfbench.topics.plasmidness.plasgraph2.results as plasgraph2_res


def convert(
    input_data_exp_fs_manager: exp_fs.DataManager,
    sample_item: smp_items.Item,
) -> None:
    """Convert plasmid probabilities to PBF format."""
    plm_res = plasgraph2_res.PlasmidProbabilities(input_data_exp_fs_manager)
    pbf_plm_res = plm_pbf_in_res.Plasmidness(
        input_data_exp_fs_manager,
    )
    plasgraph2_exp_cfg = plasgraph2_cfg.ExpConfig.from_yaml(
        input_data_exp_fs_manager.config_yaml(),
    )
    # REFACTOR (1) how to generalize that? Visitor that dispath gfa_arg
    # * probably also read get contig_dict or directly Iterable of formatted row
    # ---
    gfa_arg = plasgraph2_exp_cfg.tool_configs().arguments()[plasgraph2_cfg.Names.GFA]
    gfa_tool = asm_visitor.Tools.from_description(
        plasgraph2_cfg.Names.GFA.topic_tools()(
            gfa_arg.tool_name(),
        ).to_description(),
    )

    gfa_gz = asm_res_items.AsmGraphGZ(
        exp_fs.DataManager(
            input_data_exp_fs_manager.root_dir(),
            gfa_tool.to_description(),
            gfa_arg.exp_name(),
        ),
    )
    # ---

    plgr_df = pd.read_csv(plm_res.csv(sample_item.exp_sample_id()))
    contigs_dict = plm_pbf_in_ops.parse_gfa(
        gfa_gz.gfa_gz(sample_item.exp_sample_id()),
        gfa_tool,
    )
    for _, row in plgr_df.iterrows():
        contig_id = str(row["contig"]).split(" ")[0]
        prcr, prpl = row["chrom_score"], row["plasmid_score"]
        pred = row["label"]
        if contig_id in contigs_dict:
            contigs_dict[contig_id]["Prob_Chromosome"] = float(prcr)
            contigs_dict[contig_id]["Prob_Plasmid"] = float(prpl)
            if pred == "plasmid":
                contigs_dict[contig_id]["Prediction"] = "Plasmid"
            else:
                contigs_dict[contig_id]["Prediction"] = "Chromosome"
    contigs_df = pd.DataFrame.from_dict(contigs_dict).T

    contigs_df.to_csv(
        pbf_plm_res.tsv(sample_item.exp_sample_id()),
        columns=["Prob_Plasmid"],
        sep="\t",
        index=False,
    )
