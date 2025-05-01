"""Help application."""

import typer

import pbfbench.help.tool_tree as help_tool_tree

APP = typer.Typer(name="help", help="Help commands", rich_markup_mode="rich")
APP.command()(help_tool_tree.tool_tree)
