"""Bash experiment file system."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import pbfbench.experiment.bash.items as exp_bash_items


class Manager:
    """Bash experiment file system manager."""

    def __init__(self, script_dir: Path, date_str: str) -> None:
        """Inititialize."""
        self.__script_dir = script_dir
        self.__date_str = date_str

    def scripts_dir(self) -> Path:
        """Get script directory path."""
        return self.__script_dir

    def sbatch_script(self) -> Path:
        """Get the sbatch script file path."""
        return self.scripts_dir() / f"{self.__date_str}_sbatch.sh"

    def step_script(self, step: exp_bash_items.Steps) -> Path:
        """Get bash step status file."""
        return self.scripts_dir() / ScriptStepFilesBuilder.script_step(
            self.__date_str,
            step,
        )


class ScriptStepFilesBuilder:
    """Script step files builder."""

    EXT = "sh"

    # REFACTOR use common part with logs
    class CommandStepsPrefix(StrEnum):
        """Command steps."""

        INIT_ENV = "init_env"
        COMMAND = "command"
        CLOSE_ENV = "close_env"

        @classmethod
        def from_step(
            cls,
            step: exp_bash_items.Steps,
        ) -> ScriptStepFilesBuilder.CommandStepsPrefix:
            """Convert bash step to command step prefix."""
            match step:
                case exp_bash_items.Steps.INIT_ENV:
                    return cls.INIT_ENV
                case exp_bash_items.Steps.COMMAND:
                    return cls.COMMAND
                case exp_bash_items.Steps.CLOSE_ENV:
                    return cls.CLOSE_ENV

    @classmethod
    def script_step(cls, date_str: str, step: exp_bash_items.Steps) -> Path:
        """Get command step status filename."""
        return Path(f"{date_str}_{cls.CommandStepsPrefix.from_step(step)}.{cls.EXT}")
