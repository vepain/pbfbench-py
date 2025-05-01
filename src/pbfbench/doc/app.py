"""Autodoc application."""

# Due to typer usage:
# ruff: noqa: TC001, TC003, UP007, FBT001, FBT002, PLR0913

from __future__ import annotations

import shutil
from pathlib import Path

import typer

import pbfbench.doc.environments as doc_env

APP = typer.Typer(name="doc", help="Generate documentation", rich_markup_mode="rich")

APP.command(name="tools-envs", help="Example of how to manage the tools environments")(
    doc_env.main,
)

MAIN_DOC_DIR = Path("docs")
ENVIRONMENTS_DOC_DIR = MAIN_DOC_DIR / "environments"


@APP.command()
def clean() -> None:
    """Clean the auto documentation."""
    shutil.rmtree(ENVIRONMENTS_DOC_DIR, ignore_errors=True)


@APP.command()
def auto() -> None:
    """Generate the auto documentation."""
    ENVIRONMENTS_DOC_DIR.mkdir(parents=True, exist_ok=True)
    doc_env.main(ENVIRONMENTS_DOC_DIR)
