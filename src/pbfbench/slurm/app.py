"""SLURM applications."""

# Due to typer usage:

from __future__ import annotations

from typing import Annotated

import typer

from . import config


class Arguments:
    """SLURM app arguments."""

    ACCOUNT_NAME = typer.Argument(
        help="SLURM account name",
    )


def slurm_opts(
    account_name: Annotated[str | None, Arguments.ACCOUNT_NAME] = None,
) -> str:
    """Get default SLURM options string."""
    options_str = config.default_slurm_options(account_name)
    typer.echo(options_str)
    return options_str
