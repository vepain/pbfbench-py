"""plASgraph2 Bash script logics."""

from collections.abc import Iterator
from pathlib import Path
from typing import final

import pbfbench.abc.tool.bash as abc_tool_bash
import pbfbench.bash.items as bash_items
import pbfbench.topics.assembly.results.items as asm_res_items
import pbfbench.topics.plasmidness.plasgraph2.results as plasgraphtwo_res


@final
class GFAInputLinesBuilder(abc_tool_bash.Argument[asm_res_items.AsmGraphGZ]):
    """GFA input bash lines builder."""

    GFA_GZ_VAR = bash_items.Variable("GFA")

    OUTFILE_VAR = bash_items.Variable("OUTFILE")

    def __gfa_gz_file(self) -> Path:
        """Return a gzipped GFA path with sample name is a sh variable."""
        return self._input_result.gfa_gz(
            self._input_data_smp_sh_fs_manager.sample_dir().name,
        )

    def init_lines(self) -> Iterator[str]:
        """Get shell input init lines."""
        yield self.GFA_GZ_VAR.set(bash_items.path_to_str(self.__gfa_gz_file()))
        yield self.OUTFILE_VAR.set(
            bash_items.path_to_str(
                plasgraphtwo_res.PlasmidProbabilities(self._work_exp_fs_manager).csv(
                    self._work_smp_sh_fs_manager.sample_dir().name,
                ),
            ),
        )

    def close_lines(self) -> Iterator[str]:
        """Get shell input close lines."""
        yield from ()
