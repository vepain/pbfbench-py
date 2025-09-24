"""Init experiment logics."""

from __future__ import annotations

import logging

# import pbfbench.abc.tool.connector as abc_tool_connector
# import pbfbench.abc.topic.results as abc_topic_res
# import pbfbench.experiment.file_system as exp_fs
# import pbfbench.experiment.iter as exp_iter
# import pbfbench.samples.file_system as smp_fs
# import pbfbench.topics.binning.pangebin_once.config as pangebin_once_cfg
# import pbfbench.topics.classification.pbf_input.results as class_pbf_in_res
# import pbfbench.topics.classification.plasgraph2.plasbin_flow as plasgraph2_pbf
# import pbfbench.topics.classification.platon.convert as platon_pbf
# import pbfbench.topics.classification.visitor as class_visitor

_LOGGER = logging.getLogger(__name__)


# TODO [2025-09-19 18:41] Try to generalize
# def init(
#     data_exp_fs_manager: exp_fs.DataManager,
#     exp_config: exp_cfg.WithArguments,
#     tool_connector: abc_tool_connector.WithArguments,
# ) -> InitStats:
#     """Init pangebin-once."""
#     init_stats = InitStats.new(data_exp_fs_manager)

#     #
#     # Seeds
#     #
#     # TODO verify config exists (use already existing functions) [Not urgent]
#     # REFACTOR generalize this but e.g. plasmidness needs also the GFA tool provider
#     # REFACTOR to get the subconnector, use instead class attribute for Connector?
#     # * Connector must implement abc classmethod to_arg_paths -> Iterable[ArgPath]
#     # IDEA InitConnector with inputExpConfig type and FormattedVisitor
#     # FormattedVisitor links to FormattedResult type and convert functions
#     _tool_cfg: abc_tool_connector.WithArguments = exp_config.tool_configs()
#     seeds_arg = _tool_cfg.arguments()[pangebin_once_cfg.Names.SEEDS]
#     seeds_tool = class_visitor.Tools(seeds_arg.tool())
#     seeds_in_data_exp_fs_manager = exp_fs.DataManager(
#         data_exp_fs_manager.root_dir(),
#         seeds_tool.to_description(),
#         seeds_arg.exp_name(),
#     )
#     match seeds_tool:
#         case class_visitor.Tools.PLATON:
#             convert_function = platon_pbf.convert
#         # FIXME force match cover with return
#     samples_to_format_the_seeds = _get_samples_to_format_the_inputs(
#         data_exp_fs_manager,
#         class_pbf_in_res.Seeds(seeds_in_data_exp_fs_manager),
#         init_stats,
#     )

#     for sample in samples_to_format_the_seeds:
#         # FIXME not good usage of init stats, think in another way
#         init_stats.add_samples_to_format_the_inputs(1)
#         convert_function(
#             seeds_in_data_exp_fs_manager,
#             sample.item(),
#         )

#     #
#     # Plasmidness
#     #
#     # REFACTOR same refactor comment as above

#     class_arg = _tool_cfg.arguments()[pangebin_once_cfg.Names.PLASMIDNESS]
#     class_tool = class_visitor.Tools(class_arg.tool())
#     class_in_data_exp_fs_manager = exp_fs.DataManager(
#         data_exp_fs_manager.root_dir(),
#         class_tool.to_description(),
#         class_arg.exp_name(),
#     )
#     match class_tool:
#         case class_visitor.Tools.PLASCLASS:
#             raise NotImplementedError  # TODO implement for plasclass
#         case class_visitor.Tools.PLASGRAPH2:
#             convert_function = plasgraph2_pbf.convert
#         # REFACTOR force match cover with return

#     samples_to_format_the_plm = _get_samples_to_format_the_inputs(
#         data_exp_fs_manager,
#         class_pbf_in_res.Plasmidness(class_in_data_exp_fs_manager),
#         init_stats,
#     )
#     for sample in samples_to_format_the_plm:
#         # REFACTOR (1) here we simulate that Visitor
#         convert_function(
#             class_in_data_exp_fs_manager,
#             sample.item(),
#         )

#     return init_stats


# TODO [2025-09-19 18:31:24] invent a init object with logics (functions and classes)
# def _get_samples_to_format_the_inputs(
#     samples_to_run: list[smp_fs.RowNumberedItem],
#     formatted_result_builder: abc_topic_res.Formatted,
#     init_stats: InitStats,  # REFACTOR try to not complicate with init stats
# ) -> list[smp_fs.RowNumberedItem]:
#     """Get samples to run."""
#     # REFACTOR should be general not specific to pangebin_once tool
#     samples_to_fmt_the_inputs = list(
#         exp_iter.samples_to_format_result(
#             formatted_result_builder,
#             samples_to_run,
#         ),
#     )  # FIXME should not be recomputed but according to sample to run list
#     init_stats.add_samples_to_format_the_inputs(len(samples_to_fmt_the_inputs))

#     _LOGGER.info("Number of samples to run: %d", len(samples_to_fmt_the_inputs))
#     # REFACTOR also give the list of already formatted input?
#     return samples_to_fmt_the_inputs
