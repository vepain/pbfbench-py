"""SLURM applications."""

# Due to typer usage:

from __future__ import annotations

import typer

DEFAULT_SLURM_OPTIONS = "--mem=16 --cpus-per-task=4"


def slurm_opts() -> str:
    """Get default SLURM options string."""
    typer.echo(DEFAULT_SLURM_OPTIONS)
    return DEFAULT_SLURM_OPTIONS
