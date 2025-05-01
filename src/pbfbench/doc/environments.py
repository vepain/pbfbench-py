"""Environment auto documentation."""

from pathlib import Path
from typing import Annotated

import typer
from rich.markdown import Markdown as Md

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.abc.topic.description as abc_topic_desc
import pbfbench.experiment.file_system as exp_fs
from pbfbench import root_logging
from pbfbench.abc.tool.environments import BashEnvWrapper


def main(
    outdir: Annotated[Path, typer.Argument(help="Environment documentation directory")],
) -> None:
    """Give an example of using the environment wrapper."""
    toytopic_desc = abc_topic_desc.Description("$TOPIC", "topic-cmd")
    toytool_desc = abc_tool_desc.Description("$TOOL", "tool-cmd", toytopic_desc)
    data_fs_manager = exp_fs.Manager(Path("DATA_DIR"), toytool_desc, "$exp_name")

    md_string = "# Example of using the environment wrapper\n\n"

    outdir.mkdir(exist_ok=True)

    md_string += "\n".join(
        [
            "",
            "## Environment config",
            "",
            "Each tool is associated with a environment context script."
            f" For a topic `{toytopic_desc.name()}`"
            f" and a tool `{toytool_desc.name()}`,"
            " the environment context script file is:"
            f" `{data_fs_manager.tool_env_script_sh()}`.",
            "",
            f"The example file is in `{outdir}`",
            "",
        ],
    )

    shell_lines = "\n".join(
        [
            "# text before begin",
            "",
            f"{BashEnvWrapper.BEGIN_ENV_MAGIC_COMMENT} ====",
            "",
            "source ./virtualenv_tool/bin/activate",
            "load cluster_binary/0.1.2",
            "",
            f"{BashEnvWrapper.MID_ENV_MAGIC_COMMENT} ----",
            "",
            "deactivate",
            "unload cluster_binary/0.1.2",
            "",
            f"{BashEnvWrapper.END_ENV_MAGIC_COMMENT} ====",
            "",
            "# text after end",
            "",
        ],
    )
    tmp_script = outdir / data_fs_manager.TOOL_ENV_WRAPPER_SCRIPT_NAME
    tmp_script.write_text(shell_lines)

    md_string += "\n".join(
        [
            "",
            "## Script to describe the environment context",
            "",
            "It is constitutes in two parts:",
            "",
            "* The init part",
            "* The close part",
            "",
            "Each part is separated by magic comments.",
            "The magic comments are:",
            "",
            f"* `{BashEnvWrapper.BEGIN_ENV_MAGIC_COMMENT}`",
            f"* `{BashEnvWrapper.MID_ENV_MAGIC_COMMENT}`",
            f"* `{BashEnvWrapper.END_ENV_MAGIC_COMMENT}`",
            "",
            f"`{tmp_script}` is an example of such script:",
            "",
            "```sh",
            shell_lines,
            "```",
            "",
        ],
    )

    bash_env = BashEnvWrapper(tmp_script)

    test_wrapper_md = "\n".join(
        [
            "",
            "## Tests on the environment wrapper",
            "",
            "### Iterate over the script lines that init the environment",
            "",
            "```sh",
            "".join(bash_env.init_env_lines()) + "```",
            "",
            "### Iterate over the script lines that close the environment",
            "",
            "```sh",
            "".join(bash_env.close_env_lines()) + "```",
            "",
        ],
    )
    md_string += test_wrapper_md

    root_logging.CONSOLE.print(Md(md_string))

    readme = outdir / "README.md"
    readme.write_text(md_string)

    root_logging.CONSOLE.print(Md(f"\nThis standard output is captured in `{readme}`"))
