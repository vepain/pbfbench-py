"""PlasBin-flow classification result formatting module."""

from pathlib import Path
from typing import final

import pbfbench.abc.topic.results as abc_topic_res
import pbfbench.samples.items as smp_items
import pbfbench.samples.status as smp_status
import pbfbench.topics.classification.visitor as class_visitor


@final
class Plasmidness(abc_topic_res.Formatted):
    """Plasmidness PlasBin-flow formatted result."""

    TSV_NAME = Path("pbf_plasmidness.tsv")

    def tsv(self, sample_dirname: str | Path) -> Path:
        """Get plasmidness TSV file."""
        return self._exp_fs_manager.sample_dir(sample_dirname) / self.TSV_NAME

    def check(self, sample_item: smp_items.Item) -> smp_status.Status:
        """Check input(s)."""
        if self.tsv(sample_item.exp_sample_id()).exists():
            return smp_status.OK.OK
        return smp_status.Error.NOT_RUN


@final
class PlasmidnessVisitor(
    abc_topic_res.FormattedVisitor[class_visitor.Tools, Plasmidness],
):
    """Plasmidness result visitor."""

    # TODO[2025-09-24 12:31:12] Mimic as for result visitor (with Error)

    @classmethod
    def convert_fn(
        cls,
        tool: class_visitor.Tools,
    ) -> abc_topic_res.ConvertFn[Plasmidness] | abc_topic_res.Error:
        """Get convert function."""

        def _err(tool: class_visitor.Tools) -> abc_topic_res.Error:
            return abc_topic_res.Error(
                "Function to convert classification result to plasmidness result"
                f" is not implemented for `{tool}` ",
            )

        match tool:
            case class_visitor.Tools.PLATON:
                return _err(tool)  # FEATURE Platon plasmidness convert
            case class_visitor.Tools.PLASCLASS:
                return _err(tool)  # FEATURE PlasClass plasmidness convert
            case class_visitor.Tools.PLASGRAPH2:
                return _err(tool)  # FEATURE PlasGraph2 plasmidness convert

    @classmethod
    def result_builder(cls) -> type[Plasmidness]:
        """Get result builder."""
        return Plasmidness


@final
class Seeds(abc_topic_res.Formatted):
    """Seeds PlasBin-flow formatted result."""

    TSV_NAME = Path("pbf_seeds.tsv")

    def tsv(self, sample_dirname: str | Path) -> Path:
        """Get seeds TSV file."""
        return self._exp_fs_manager.sample_dir(sample_dirname) / self.TSV_NAME

    def check(self, sample_item: smp_items.Item) -> smp_status.Status:
        """Check input(s)."""
        if self.tsv(sample_item.exp_sample_id()).exists():
            return smp_status.OK.OK
        return smp_status.Error.NOT_RUN


@final
class SeedsVisitor(abc_topic_res.FormattedVisitor[class_visitor.Tools, Seeds]):
    """Seeds result visitor."""

    @classmethod
    def convert_fn(
        cls,
        tool: class_visitor.Tools,
    ) -> abc_topic_res.ConvertFn[Seeds] | abc_topic_res.Error:
        """Get convert function."""

        def _err(tool: class_visitor.Tools) -> abc_topic_res.Error:
            return abc_topic_res.Error(
                "Function to convert classification result to plasmidness result"
                f" is not implemented for `{tool}` ",
            )

        match tool:
            case class_visitor.Tools.PLATON:
                return _err(tool)  # FEATURE Platon seeds convert
            case class_visitor.Tools.PLASCLASS:
                return _err(tool)  # FEATURE PlasClass seeds convert
            case class_visitor.Tools.PLASGRAPH2:
                return _err(tool)  # FEATURE PlasGraph2 seeds convert

    @classmethod
    def result_builder(cls) -> type[Seeds]:
        """Get result builder."""
        return Seeds
