"""Experiment input/output logics."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import final

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.experiment.bash.file_system as exp_bash_fs
import pbfbench.experiment.slurm.file_system as exp_slurm_fs
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.items as smp_items


class ManagerBase:
    """Experiment file system manager base."""

    CONFIG_YAML_NAME = Path("config.yaml")
    DATE_TXT_NAME = Path("date.txt")

    SCRIPT_DIR_NAME = Path("scripts")

    def __init__(
        self,
        root_directory_path: Path,
        tool_description: abc_tool_desc.Description,
        experiment_name: str,
    ) -> None:
        """Initialize."""
        self._root_directory_path = root_directory_path
        self._tool_description = tool_description
        self._experiment_name = experiment_name
        self._date_str = self._get_date_str()
        self._script_fs_manager = exp_bash_fs.Manager(
            self.exp_dir() / self.SCRIPT_DIR_NAME,
            self._date_str,
        )

    def _get_date_str(self) -> str:
        """Get date string."""
        if not self.date_txt().exists():
            return _get_today_format_string()
        with self.date_txt().open("r") as f_in:
            return f_in.read().strip()

    def tool_description(self) -> abc_tool_desc.Description:
        """Get tool description."""
        return self._tool_description

    def experiment_name(self) -> str:
        """Get experiment name."""
        return self._experiment_name

    def root_dir(self) -> Path:
        """Get root directory path."""
        return self._root_directory_path

    def topic_dir(self) -> Path:
        """Get topic directory path."""
        return self._root_directory_path / self._tool_description.topic().name()

    def tool_dir(self) -> Path:
        """Get tool directory path."""
        return self.topic_dir() / self._tool_description.name()

    def exp_dir(self) -> Path:
        """Get experiment directory path."""
        return self.tool_dir() / self._experiment_name

    #
    # Date
    #
    def date_str(self) -> str:
        """Get date string."""
        return self._date_str

    def date_txt(self) -> Path:
        """Get the file containing the experiment date."""
        return self.exp_dir() / self.DATE_TXT_NAME

    #
    # Experiment files
    #
    def config_yaml(self) -> Path:
        """Get config file."""
        return self.exp_dir() / self.CONFIG_YAML_NAME

    #
    # Sbatch scripts
    #
    def scripts_fs_manager(self) -> exp_bash_fs.Manager:
        """Get experiment scripts file system manager."""
        return self._script_fs_manager

    #
    # Sample experiment directories
    #
    def sample_dir(self, sample_dirname: str | Path) -> Path:
        """Get sample experiment directory path."""
        return self.exp_dir() / sample_dirname

    def sample_fs_manager(self, sample_item: smp_items.Item) -> smp_fs.Manager:
        """Get sample experiment directory path."""
        return smp_fs.Manager(self.exp_dir() / sample_item.exp_sample_id())


@final
class DataManager(ManagerBase):
    """Data experiment manager."""

    SAMPLES_TSV_NAME = Path("samples.tsv")

    TOOL_ENV_WRAPPER_SCRIPT_NAME = Path("env_wrapper.sh")

    ERRORS_TSV_NAME = Path("errors.tsv")

    def samples_tsv(self) -> Path:
        """Get samples TSV file."""
        return self.root_dir() / self.SAMPLES_TSV_NAME

    def tool_env_script_sh(self) -> Path:
        """Get tool environment script file."""
        return self.tool_dir() / self.TOOL_ENV_WRAPPER_SCRIPT_NAME

    def errors_tsv(self) -> Path:
        """Get errors file."""
        return self.exp_dir() / self.ERRORS_TSV_NAME


@final
class WorkManager(ManagerBase):
    """Work experiment manager."""

    TMP_SLURM_LOG_DIR_NAME = Path("logs")

    def __init__(
        self,
        root_directory_path: Path,
        tool_description: abc_tool_desc.Description,
        experiment_name: str,
    ) -> None:
        super().__init__(root_directory_path, tool_description, experiment_name)
        self.__slurm_log_fs_manager = exp_slurm_fs.LogsManager(
            self.exp_dir() / self.TMP_SLURM_LOG_DIR_NAME,
        )

    #
    # Tmp sbatch logs
    #
    def slurm_log_fs_manager(self) -> exp_slurm_fs.LogsManager:
        """Get slurm logs manager."""
        return self.__slurm_log_fs_manager


def _get_today_format_string() -> str:
    """Get date format string."""
    return datetime.now(tz=UTC).strftime("%Y-%m-%d_%H-%M-%S")


def data_and_working_managers(
    data_dir: Path,
    working_dir: Path,
    tool_description: abc_tool_desc.Description,
    experiment_name: str,
) -> tuple[DataManager, WorkManager]:
    """Get data and working managers."""
    return (
        DataManager(data_dir, tool_description, experiment_name),
        WorkManager(working_dir, tool_description, experiment_name),
    )
