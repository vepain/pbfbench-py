"""plASgraph2 Bash script logics."""

from collections.abc import Iterator
from pathlib import Path
from typing import final

import pbfbench.abc.tool.shell as abc_tool_shell
import pbfbench.shell as sh
import pbfbench.topics.assembly.results.items as asm_res_items
import pbfbench.topics.plasmidness.plasgraphtwo.results as plasgraphtwo_res


@final
class GFAInputLinesBuilder(
    abc_tool_shell.ArgBashLinesBuilder[asm_res_items.AsmGraphGZ],
):
    """GFA input bash lines builder."""

    GFA_GZ_VAR = sh.Variable("GFA")

    OUTFILE_VAR = sh.Variable("OUTFILE")

    def __gfa_gz_file(self) -> Path:
        """Return a gzipped GFA path with sample name is a sh variable."""
        return self._input_result.gfa_gz(
            self._input_data_smp_sh_fs_manager.sample_dir().name,
        )

    def init_lines(self) -> Iterator[str]:
        """Get shell input init lines."""
        yield self.GFA_GZ_VAR.set(sh.path_to_str(self.__gfa_gz_file()))
        yield self.OUTFILE_VAR.set(
            sh.path_to_str(
                plasgraphtwo_res.PlasmidProbabilities(self._work_exp_fs_manager).csv(
                    self._work_smp_sh_fs_manager.sample_dir().name,
                ),
            ),
        )

    def close_lines(self) -> Iterator[str]:
        """Get shell input close lines."""
        yield from ()
