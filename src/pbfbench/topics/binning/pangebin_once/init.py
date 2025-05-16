"""Init experiment logics."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pbfbench.abc.tool.config as abc_tool_cfg
import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.abc.topic.results.items as abc_topic_res_items
import pbfbench.experiment.config as exp_cfg
import pbfbench.experiment.file_system as exp_fs
import pbfbench.experiment.iter as exp_iter
import pbfbench.samples.file_system as smp_fs
import pbfbench.topics.binning.pangebin_once.config as pangebin_once_cfg
import pbfbench.topics.plasmidness.pbf_input.results as plm_pbf_in_res
import pbfbench.topics.plasmidness.plasgraph2.plasbin_flow as plasgraph2_pbf
import pbfbench.topics.plasmidness.visitor as plm_visitor
import pbfbench.topics.seeds.pbf_input.results as seeds_pbf_in_res
import pbfbench.topics.seeds.platon.plasbin_flow as platon_pbf
import pbfbench.topics.seeds.visitor as seeds_visitor

if TYPE_CHECKING:
    from collections.abc import Iterable


_LOGGER = logging.getLogger(__name__)


class InitStats:
    """Experiment init stats."""

    @classmethod
    def new(cls, data_exp_fs_manager: exp_fs.DataManager) -> InitStats:
        """Create new init stats."""
        with smp_fs.TSVReader.open(data_exp_fs_manager.samples_tsv()) as smp_tsv_in:
            number_of_samples = sum(1 for _ in smp_tsv_in.iter_row_numbered_items())
        return cls(number_of_samples, 0, None, None)

    def __init__(
        self,
        number_of_samples: int,
        number_of_samples_to_format_the_input: int,
        samples_with_missing_inputs: Iterable[str] | None,
        samples_with_errors: Iterable[str] | None,
    ) -> None:
        """Init init stats."""
        self.__number_of_samples = number_of_samples
        self.__number_of_samples_to_format_the_inputs = (
            number_of_samples_to_format_the_input
        )
        self.__samples_with_missing_inputs = (
            list(samples_with_missing_inputs)
            if samples_with_missing_inputs is not None
            else []
        )
        self.__samples_with_errors = (
            list(samples_with_errors) if samples_with_errors is not None else []
        )

    def number_of_samples(self) -> int:
        """Get number of samples."""
        return self.__number_of_samples

    def number_of_samples_to_format_the_inputs(self) -> int:
        """Get number of samples to format the inputs."""
        return self.__number_of_samples_to_format_the_inputs

    def samples_with_missing_inputs(self) -> list[str]:
        """Get samples with missing inputs."""
        return self.__samples_with_missing_inputs

    def samples_with_errors(self) -> list[str]:
        """Get samples with errors."""
        return self.__samples_with_errors

    def add_samples_to_format_the_inputs(self, addition: int) -> None:
        """Add samples to format the inputs."""
        self.__number_of_samples_to_format_the_inputs += addition


# REFACTOR try to generalize
def init(
    data_exp_fs_manager: exp_fs.DataManager,
    exp_config: exp_cfg.ConfigWithArguments,
    tool_connector: abc_tool_visitor.ConnectorWithArguments,
) -> InitStats:
    """Init pangebin-once."""
    init_stats = InitStats.new(data_exp_fs_manager)

    #
    # Seeds
    #
    # TODO verify config exists (use already existing functions) [Not urgent]
    # REFACTOR generalize this but e.g. plasmidness needs also the GFA tool provider
    # REFACTOR to get the subconnector, use instead class attribute for Connector?
    # * Connector must implement abc classmethod to_arg_paths -> Iterable[ArgPath]
    # REFACTOR IDEA InitConnector with inputExpConfig type and FormattedVisitor
    # FormattedVisitor links to FormattedResult type and convert functions
    _tool_cfg: abc_tool_cfg.ConfigWithArguments = exp_config.tool_configs()
    seeds_arg = _tool_cfg.arguments()[pangebin_once_cfg.Names.SEEDS]
    seeds_tool = seeds_visitor.Tools(seeds_arg.tool_name())
    seeds_in_data_exp_fs_manager = exp_fs.DataManager(
        data_exp_fs_manager.root_dir(),
        seeds_tool.to_description(),
        seeds_arg.exp_name(),
    )
    samples_to_format_the_seeds = _get_samples_to_format_the_inputs(
        data_exp_fs_manager,
        seeds_pbf_in_res.Seeds(seeds_in_data_exp_fs_manager),
        init_stats,
    )
    match seeds_tool:
        case seeds_visitor.Tools.PLATON:
            convert_function = platon_pbf.convert
        # FIXME force match cover with return

    for sample in samples_to_format_the_seeds:
        # FIXME not good usage of init stats, think in another way
        init_stats.add_samples_to_format_the_inputs(1)
        convert_function(
            seeds_in_data_exp_fs_manager,
            sample.item(),
        )

    #
    # Plasmidness
    #
    # REFACTOR same refactor comment as above

    plm_arg = _tool_cfg.arguments()[pangebin_once_cfg.Names.PLASMIDNESS]
    plm_tool = plm_visitor.Tools(plm_arg.tool_name())
    plm_in_data_exp_fs_manager = exp_fs.DataManager(
        data_exp_fs_manager.root_dir(),
        plm_tool.to_description(),
        plm_arg.exp_name(),
    )
    match plm_tool:
        case plm_visitor.Tools.PLASCLASS:
            raise NotImplementedError  # TODO implement for plasclass
        case plm_visitor.Tools.PLASGRAPH2:
            convert_function = plasgraph2_pbf.convert
        # REFACTOR force match cover with return

    samples_to_format_the_plm = _get_samples_to_format_the_inputs(
        data_exp_fs_manager,
        plm_pbf_in_res.Plasmidness(plm_in_data_exp_fs_manager),
        init_stats,
    )
    for sample in samples_to_format_the_plm:
        # REFACTOR (1) here we simulate that Visitor
        convert_function(
            plm_in_data_exp_fs_manager,
            sample.item(),
        )

    return init_stats


def _get_samples_to_format_the_inputs(
    data_exp_fs_manager: exp_fs.DataManager,
    formatted_result_builder: abc_topic_res_items.Formatted,
    init_stats: InitStats,
) -> list[smp_fs.RowNumberedItem]:
    """Get samples to run."""
    with smp_fs.TSVReader.open(data_exp_fs_manager.samples_tsv()) as smp_tsv_in:
        samples_to_fmt_the_inputs = list(
            exp_iter.samples_to_format_result(
                formatted_result_builder,
                smp_tsv_in.iter_row_numbered_items(),
            ),
        )
    init_stats.add_samples_to_format_the_inputs(len(samples_to_fmt_the_inputs))

    _LOGGER.info("Number of samples to run: %d", len(samples_to_fmt_the_inputs))

    return samples_to_fmt_the_inputs
