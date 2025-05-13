"""Init experiment logics."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pbfbench.abc.tool.visitor as abc_tool_visitor
import pbfbench.experiment.config as exp_cfg
import pbfbench.experiment.file_system as exp_fs
import pbfbench.experiment.iter as exp_iter
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.items as smp_items
import pbfbench.topics.binning.pangebin_once.config as pangebin_once_cfg
import pbfbench.topics.plasmidness.pbf_input.results as plm_pbf_in_res
import pbfbench.topics.plasmidness.plasgraph2.plasbin_flow as plasgraph2_pbf
import pbfbench.topics.plasmidness.visitor as plm_visitor
import pbfbench.topics.seeds.pbf_input.results as seeds_pbf_in_res
import pbfbench.topics.seeds.platon.plasbin_flow as platon_pbf
import pbfbench.topics.seeds.visitor as seeds_visitor

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


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
    pbf_seeds_res = seeds_pbf_in_res.Seeds(
        data_exp_fs_manager,
        tool_connector.description(),
    )
    samples_to_format_the_seeds = _get_samples_to_format_the_inputs(
        data_exp_fs_manager,
        init_stats,
        lambda _, smp: pbf_seeds_res.tsv(smp.exp_sample_id()).exists(),
    )
    # REFACTOR generalize this but e.g. plasmidness needs also the GFA tool provider
    # REFACTOR to get the subconnector, use instead class attribute for Connector?
    # * Connector must implement abc classmethod to_arg_paths -> Iterable[ArgPath]
    seeds_arg = exp_config.tool_configs().arguments()[pangebin_once_cfg.Names.SEEDS]
    seeds_tool = seeds_visitor.Tools(seeds_arg.tool_name())
    seeds_in_data_exp_fs_manager = exp_fs.DataManager(
        data_exp_fs_manager.root_dir(),
        seeds_tool.to_description(),
        seeds_arg.exp_name(),
    )
    match seeds_tool:
        case seeds_visitor.Tools.PLATON:
            convert_function = platon_pbf.convert
        # REFACTOR force match cover with return

    for sample in samples_to_format_the_seeds:
        # REFACTOR not good usage of init stats, think in another way
        init_stats.add_samples_to_format_the_inputs(1)
        convert_function(
            seeds_in_data_exp_fs_manager,
            sample.item(),
            tool_connector.description(),  # REFACTOR change that to Formatted
        )

    #
    # Plasmidness
    #
    pbf_plm_res = plm_pbf_in_res.Plasmidness(
        data_exp_fs_manager,
        tool_connector.description(),
    )
    samples_to_format_the_plm = _get_samples_to_format_the_inputs(
        data_exp_fs_manager,
        init_stats,
        lambda _, smp: pbf_plm_res.tsv(smp.exp_sample_id()).exists(),
    )
    # REFACTOR same refactor comment as above
    plm_arg = exp_config.tool_configs().arguments()[pangebin_once_cfg.Names.PLASMIDNESS]
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
    for sample in samples_to_format_the_plm:
        # REFACTOR (1) here we simulate that Visitor
        convert_function(
            plm_in_data_exp_fs_manager,
            sample.item(),
            tool_connector.description(),
        )

    return init_stats


def _get_samples_to_format_the_inputs(
    data_exp_fs_manager: exp_fs.DataManager,
    init_stats: InitStats,
    fn_format_result_exists: Callable[[exp_fs.DataManager, smp_items.Item], bool],
) -> list[smp_fs.RowNumberedItem]:
    """Get samples to run."""
    with smp_fs.TSVReader.open(data_exp_fs_manager.samples_tsv()) as smp_tsv_in:
        samples_to_fmt_the_inputs = list(
            exp_iter.samples_to_format_result(
                data_exp_fs_manager,
                smp_tsv_in.iter_row_numbered_items(),
                fn_format_result_exists,
            ),
        )
    init_stats.add_samples_to_format_the_inputs(len(samples_to_fmt_the_inputs))

    _LOGGER.info("Number of samples to run: %d", len(samples_to_fmt_the_inputs))

    return samples_to_fmt_the_inputs
