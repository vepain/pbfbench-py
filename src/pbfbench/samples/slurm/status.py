"""Samples slurm status logics."""

from typing import Self, final

import pbfbench.experiment.slurm.status as exp_slurm_status
from pbfbench.yaml_interface import YAMLInterface


@final
class CommandStepsProcess(YAMLInterface):
    """Command steps process status."""

    INIT_ENV_KEY = "init_env"
    COMMAND_KEY = "command"
    CLOSE_ENV_KEY = "close_env"

    @classmethod
    def from_yaml_load(cls, pyyaml_obj: dict[str, str]) -> Self:
        """Convert pyyaml object to self."""
        return cls(
            exp_slurm_status.ScriptSteps(pyyaml_obj[cls.INIT_ENV_KEY]),
            exp_slurm_status.ScriptSteps(pyyaml_obj[cls.COMMAND_KEY]),
            exp_slurm_status.ScriptSteps(pyyaml_obj[cls.CLOSE_ENV_KEY]),
        )

    def __init__(
        self,
        init_env: exp_slurm_status.ScriptSteps,
        command: exp_slurm_status.ScriptSteps,
        close_env: exp_slurm_status.ScriptSteps,
    ) -> None:
        """Initialize."""
        self.__init_env = init_env
        self.__command = command
        self.__close_env = close_env

    def init_env(self) -> exp_slurm_status.ScriptSteps:
        """Get init env command step."""
        return self.__init_env

    def command(self) -> exp_slurm_status.ScriptSteps:
        """Get command command step."""
        return self.__command

    def close_env(self) -> exp_slurm_status.ScriptSteps:
        """Get close env command step."""
        return self.__close_env

    def to_yaml_dump(self) -> dict[str, str]:
        """Convert self to pyyaml object."""
        return {
            self.INIT_ENV_KEY: self.__init_env.value,
            self.COMMAND_KEY: self.__command.value,
            self.CLOSE_ENV_KEY: self.__close_env.value,
        }
