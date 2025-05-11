"""plASgraph2 results."""

from __future__ import annotations

from pathlib import Path
from typing import final

import pbfbench.abc.topic.results.items as topic_res_items


@final
class PlasmidProbabilities(topic_res_items.Original):
    """Plasmid probabilities result."""

    CSV_NAME = Path("plasmid_probabilities.csv")

    def csv(self, sample_dirname: str | Path) -> Path:
        """Get plasmid probabilities CSV file."""
        return self._fs_manager.sample_dir(sample_dirname) / self.CSV_NAME
