"""Slurm configs."""

from __future__ import annotations


def default_slurm_options(account_name: str | None) -> str:
    """Return default SLURM options."""
    account_opt = "" if account_name is None else f"--account={account_name}"
    return f"--mem=4096 --cpus-per-task=4 --time=1:00:00 {account_opt}"
