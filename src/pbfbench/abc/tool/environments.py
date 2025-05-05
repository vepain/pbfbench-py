"""Tools environment logic.

Some tools require a specific environment,
such as a specific virtualenv, setting binary paths etc.

This module provides such logic.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

_LOGGER = logging.getLogger(__name__)


class BashEnvWrapper:
    """Wrapper to run a bash script in a specific environment."""

    BEGIN_ENV_MAGIC_COMMENT = "# PBFBENCH BEGIN_ENV"
    MID_ENV_MAGIC_COMMENT = "# PBFBENCH MID_ENV"
    END_ENV_MAGIC_COMMENT = "# PBFBENCH END_ENV"

    def __init__(self, script_path: Path) -> None:
        self.__script_path = script_path
        self.__begin_line_index: int = 0
        self.__mid_line_index: int = 0
        self.__end_line_index: int = 0
        self.__index_script()

    def init_env_lines(self) -> Iterator[str]:
        """Iterate over the script lines that init the environment."""
        with self.__script_path.open("r") as f_in_script:
            iter_lines = iter(f_in_script)
            line = next(iter_lines)
            k = 0
            # Skip before the begin magic comment
            while k < self.__begin_line_index:
                line = next(iter_lines)
                k += 1
            # Yield the lines until the mid magic comment
            while k < self.__mid_line_index:
                yield line.rstrip()
                line = next(iter_lines)
                k += 1
            # Add the mid magic comment
            yield line.rstrip()

    def close_env_lines(self) -> Iterator[str]:
        """Iterate over the script lines that close the environment."""
        with self.__script_path.open("r") as f_in_script:
            iter_lines = iter(f_in_script)
            line = next(iter_lines)
            k = 0
            # Skip before the mid magic comment
            while k < self.__mid_line_index:
                line = next(iter_lines)
                k += 1
            # Yield the lines until the end magic comment
            while k < self.__end_line_index:
                yield line.rstrip()
                line = next(iter_lines)
                k += 1
            # Add the end magic comment
            yield line.rstrip()

    def __index_script(self) -> None:
        """Index the script lines."""
        with self.__script_path.open("r") as f_in_script:
            k = 0
            iter_lines = iter(f_in_script)
            line = next(iter_lines, None)
            while line is not None and not line.startswith(
                self.BEGIN_ENV_MAGIC_COMMENT,
            ):
                line = next(iter_lines, None)
                k += 1
            if line is None:
                _err_message = self.__magic_comment_not_found_msg(
                    self.BEGIN_ENV_MAGIC_COMMENT,
                )
                _LOGGER.critical(_err_message)
                raise RuntimeError(_err_message)
            self.__begin_line_index = k
            line = next(iter_lines, None)
            k += 1
            while line is not None and not line.startswith(
                self.MID_ENV_MAGIC_COMMENT,
            ):
                line = next(iter_lines, None)
                k += 1
            if line is None:
                _err_message = self.__magic_comment_not_found_msg(
                    self.MID_ENV_MAGIC_COMMENT,
                )
                _LOGGER.critical(_err_message)
                raise RuntimeError(_err_message)
            self.__mid_line_index = k
            line = next(iter_lines, None)
            k += 1
            while line is not None and not line.startswith(
                self.END_ENV_MAGIC_COMMENT,
            ):
                line = next(iter_lines, None)
                k += 1
            if line is None:
                _err_message = self.__magic_comment_not_found_msg(
                    self.END_ENV_MAGIC_COMMENT,
                )
                _LOGGER.critical(_err_message)
                raise RuntimeError(_err_message)
            self.__end_line_index = k

    def __magic_comment_not_found_msg(self, magic_comment: str) -> str:
        return f"Could not find magic comment {magic_comment} in {self.__script_path}"
