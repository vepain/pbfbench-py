"""Run SLURM job logics."""

import logging
import subprocess

import typer

import pbfbench.experiment.bash.manager as bash_manager
import pbfbench.slurm.bash as slurm_bash
from pbfbench import subprocess_lib

_LOGGER = logging.getLogger(__name__)


def run(sh_manager: bash_manager.Manager) -> None:
    """Run sbatch script."""
    cmd_path = subprocess_lib.command_path(slurm_bash.SBATCH_CMD)
    result = subprocess.run(  # noqa: S603
        [str(x) for x in [cmd_path, sh_manager.work_sh_fs_manager().sbatch_script()]],
        capture_output=True,
        text=True,
        check=False,
    )
    _LOGGER.debug("%s stdout: %s", slurm_bash.SBATCH_CMD, result.stdout)
    _LOGGER.debug("%s stderr: %s", slurm_bash.SBATCH_CMD, result.stderr)
    if result.returncode != 0:
        _LOGGER.critical("Running sbatch script failed:\n%s", result.stderr)
        raise typer.Exit(1)
