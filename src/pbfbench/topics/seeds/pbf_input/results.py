"""PlasBin-flow seeds result formatting module."""

from pathlib import Path
from typing import final

import pbfbench.abc.topic.results.items as abc_topic_res_items
import pbfbench.abc.topic.results.visitors as topic_res_visitors
import pbfbench.samples.items as smp_items
import pbfbench.samples.status as smp_status


@final
class Seeds(abc_topic_res_items.Formatted):
    """Seeds PlasBin-flow formatted result."""

    TSV_NAME = Path("pbf_seeds.tsv")

    def tsv(self, sample_dirname: str | Path) -> Path:
        """Get seeds TSV file."""
        return self._exp_fs_manager.sample_dir(sample_dirname) / self.TSV_NAME

    def check(self, sample_item: smp_items.Item) -> smp_status.Status:
        """Check input(s)."""
        if self.tsv(sample_item.exp_sample_id()).exists():
            return smp_status.OKStatus.OK
        return smp_status.ErrorStatus.NOT_RUN


@final
class SeedsVisitor(topic_res_visitors.Formatted):
    """Seeds result visitor."""

    @classmethod
    def result_builder(cls) -> type[Seeds]:
        """Get result builder."""
        return Seeds
