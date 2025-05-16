"""Concrete tool Bash script logics."""

from collections.abc import Iterator
from pathlib import Path
from typing import final

import pbfbench.abc.tool.bash as abc_tool_bash
import pbfbench.bash.items as bash_items
import pbfbench.topics.assembly.results.items as asm_res_items
import pbfbench.topics.plasmidness.pbf_input.results as plm_pbf_in_res
import pbfbench.topics.seeds.pbf_input.results as seeds_pbf_in_res


@final
class GFAInputLinesBuilder(abc_tool_bash.Argument[asm_res_items.AsmGraphGZ]):
    """GFA input bash lines builder."""

    GFA_GZ_VAR = bash_items.Variable("GFA")

    def __gfa_gz_file(self) -> Path:
        """Return a gzipped GFA path with sample name is a sh variable."""
        return self._input_result.gfa_gz(
            self._input_data_smp_sh_fs_manager.sample_dir().name,
        )

    def init_lines(self) -> Iterator[str]:
        """Get shell input init lines."""
        yield self.GFA_GZ_VAR.set(bash_items.path_to_str(self.__gfa_gz_file()))

    def close_lines(self) -> Iterator[str]:
        """Get shell input close lines."""
        yield from ()


@final
class SeedsInputLinesBuilder(
    abc_tool_bash.Argument[seeds_pbf_in_res.Seeds],
):
    """Seeds input bash lines builder."""

    SEEDS_VAR = bash_items.Variable("SEEDS")

    def __plasbin_seeds_file(self) -> Path:
        """Return a gzipped GFA path with sample name is a sh variable."""
        return self._input_result.tsv(
            self._input_data_smp_sh_fs_manager.sample_dir().name,
        )

    def init_lines(self) -> Iterator[str]:
        """Get shell input init lines."""
        yield self.SEEDS_VAR.set(bash_items.path_to_str(self.__plasbin_seeds_file()))

    def close_lines(self) -> Iterator[str]:
        """Get shell input close lines."""
        yield from ()


@final
class PlasmidnessInputLinesBuilder(
    abc_tool_bash.Argument[plm_pbf_in_res.Plasmidness],
):
    """Plasmidness input bash lines builder."""

    PLASMIDNESS_VAR = bash_items.Variable("PLASMIDNESS")

    def __plasbin_plasmidness_file(self) -> Path:
        """Return a gzipped GFA path with sample name is a sh variable."""
        return self._input_result.tsv(
            self._input_data_smp_sh_fs_manager.sample_dir().name,
        )

    def init_lines(self) -> Iterator[str]:
        """Get shell input init lines."""
        yield self.PLASMIDNESS_VAR.set(
            bash_items.path_to_str(self.__plasbin_plasmidness_file()),
        )

    def close_lines(self) -> Iterator[str]:
        """Get shell input close lines."""
        yield from ()
