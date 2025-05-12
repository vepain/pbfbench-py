"""Experiment input/output logics."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import final

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.items as smp_items
import pbfbench.slurm.file_system as slurm_fs


# FIXME the refactor making the diff between data and work fs manager
class ManagerBase(ABC):
    """Experiment file system manager base."""

    SCRIPT_DIR_NAME = Path("scripts")

    ERRORS_TSV_NAME = Path("errors.tsv")
    CONFIG_YAML_NAME = Path("config.yaml")

    DATE_TXT_NAME = Path("date.txt")

    def __init__(
        self,
        root_directory_path: Path,
        tool_description: abc_tool_desc.Description,
        experiment_name: str,
    ) -> None:
        """Initialize."""
        self.__root_directory_path = root_directory_path
        self.__tool_description = tool_description
        self.__experiment_name = experiment_name
        self.__date_str = self.date_str()

    @abstractmethod
    def _get_date_str(self) -> str:
        """Get date string."""
        raise NotImplementedError

    def tool_description(self) -> abc_tool_desc.Description:
        """Get tool description."""
        return self.__tool_description

    def experiment_name(self) -> str:
        """Get experiment name."""
        return self.__experiment_name

    def root_dir(self) -> Path:
        """Get root directory path."""
        return self.__root_directory_path

    def topic_dir(self) -> Path:
        """Get topic directory path."""
        return self.__root_directory_path / self.__tool_description.topic().name()

    def tool_dir(self) -> Path:
        """Get tool directory path."""
        return self.topic_dir() / self.__tool_description.name()

    def exp_dir(self) -> Path:
        """Get experiment directory path."""
        return self.tool_dir() / self.__experiment_name

    #
    # Date
    #
    def date_str(self) -> str:
        """Get date string."""
        return self.__date_str

    def date_txt(self) -> Path:
        """Get the file containing the experiment date."""
        return self.exp_dir() / self.DATE_TXT_NAME

    #
    # Experiment files
    #
    def config_yaml(self) -> Path:
        """Get config file."""
        return self.exp_dir() / self.CONFIG_YAML_NAME

    def errors_tsv(self) -> Path:
        """Get errors file."""
        return self.exp_dir() / self.ERRORS_TSV_NAME

    #
    # Sbatch scripts
    #
    def scripts_dir(self) -> Path:
        """Get experiment scripts directory path."""
        return self.exp_dir() / self.SCRIPT_DIR_NAME

    def sbatch_sh_script(self) -> Path:
        """Get the sbatch script file path."""
        return self.scripts_dir() / f"{self.__date_str}_sbatch.sh"

    def command_sh_script(self) -> Path:
        """Get the command script file path."""
        return self.scripts_dir() / f"{self.__date_str}_command.sh"

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

    TOOL_ENV_WRAPPER_SCRIPT_NAME = Path("env_wrapper.sh")

    SAMPLES_TSV_NAME = Path("samples.tsv")

    def _get_date_str(self) -> str:
        """Get date string."""
        if not self.date_txt().exists():
            return _get_today_format_string()
        with self.date_txt().open("r") as f_in:
            return f_in.read().strip()

    def samples_tsv(self) -> Path:
        """Get samples TSV file."""
        return self.root_dir() / self.SAMPLES_TSV_NAME

    #
    # Tool files
    #
    def tool_env_script_sh(self) -> Path:
        """Get tool environment script file."""
        return self.tool_dir() / self.TOOL_ENV_WRAPPER_SCRIPT_NAME


@final
class WorkManager(ManagerBase):
    """Work experiment manager."""

    TMP_SLURM_LOG_DIR_NAME = Path("logs")

    def _get_date_str(self) -> str:
        """Get date string."""
        return _get_today_format_string()

    #
    # Tmp sbatch logs
    #
    def tmp_slurm_logs_dir(self) -> Path:
        """Get tmp slurm logs directory path."""
        return self.exp_dir() / self.TMP_SLURM_LOG_DIR_NAME

    def array_job_id_file(self) -> Path:
        """Get array job id file."""
        return self.tmp_slurm_logs_dir() / slurm_fs.LogFiles.ARRAY_JOB_ID_FILENAME

    def sbatch_file_regex(self, job_id: str) -> Path:
        """Get sbatch file regex."""
        return self.tmp_slurm_logs_dir() / slurm_fs.LogFiles.filename_builder(
            job_id,
            "*",
        )

    def sbatch_out_file(self, job_id: str) -> Path:
        """Get sbatch out file."""
        return self.tmp_slurm_logs_dir() / slurm_fs.LogFiles.out_filename(
            job_id,
        )

    def sbatch_err_file(self, job_id: str) -> Path:
        """Get sbatch err file."""
        return self.tmp_slurm_logs_dir() / slurm_fs.LogFiles.err_filename(
            job_id,
        )

    def sbatch_init_env_error_file(self, job_id: str) -> Path:
        """Get sbatch init env error file."""
        return self.tmp_slurm_logs_dir() / slurm_fs.LogFiles.init_env_error_filename(
            job_id,
        )

    def sbatch_command_error_file(self, job_id: str) -> Path:
        """Get sbatch command error file."""
        return self.tmp_slurm_logs_dir() / slurm_fs.LogFiles.command_error_filename(
            job_id,
        )

    def sbatch_close_env_error_file(self, job_id: str) -> Path:
        """Get sbatch close env error file."""
        return self.tmp_slurm_logs_dir() / slurm_fs.LogFiles.close_env_error_filename(
            job_id,
        )

    def sbatch_end_file(self, job_id: str) -> Path:
        """Get sbatch end file."""
        return self.tmp_slurm_logs_dir() / slurm_fs.LogFiles.end_filename(
            job_id,
        )


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


def write_formatted_exp_date(work_exp_fs_manager: WorkManager) -> None:
    """Write formatted experiment date."""
    with work_exp_fs_manager.date_txt().open("w") as f_out:
        f_out.write(work_exp_fs_manager.date_str() + "\n")


def get_array_job_id_from_file(work_exp_fs_manager: WorkManager) -> str:
    """Get job id from file."""
    with work_exp_fs_manager.array_job_id_file().open("r") as in_array_job_id:
        return in_array_job_id.read().strip()
