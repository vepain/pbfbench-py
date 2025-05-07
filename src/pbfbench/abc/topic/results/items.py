"""Abstract tools results items module."""

from abc import ABC, abstractmethod

import pbfbench.abc.app as abc_app
import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.items as smp_items
import pbfbench.samples.status as smp_status


class Result(ABC):
    """Result base."""

    @classmethod
    @abstractmethod
    def final_subcommand(cls) -> abc_app.FinalCommands:
        """Get final subcommand."""
        raise NotImplementedError

    def __init__(self, fs_manager: exp_fs.Manager) -> None:
        """Initialize."""
        self._fs_manager = fs_manager

    def fs_manager(self) -> exp_fs.Manager:
        """Get file system manager."""
        return self._fs_manager

    @abstractmethod
    def check(self, sample_item: smp_items.Item) -> smp_status.Status:
        """Check input(s)."""
        raise NotImplementedError

    @abstractmethod
    def origin_command(self) -> str:
        """Get original command."""
        raise NotImplementedError


class Original(Result):
    """Original result."""

    @classmethod
    def final_subcommand(cls) -> abc_app.FinalCommands:
        """Get final subcommand."""
        return abc_app.FinalCommands.RUN

    def check(self, sample_item: smp_items.Item) -> smp_status.Status:
        """Check input(s)."""
        return smp_status.get_status(self._fs_manager.sample_fs_manager(sample_item))

    def origin_command(self) -> str:
        """Get original command."""
        return (
            "pbfbench"
            f" {self.fs_manager().tool_description().topic().cmd()}"
            f" {self.fs_manager().tool_description().cmd()}"
            f" {self.final_subcommand()}"
            " --help"
        )


class Formatted(Result):
    """Formatted result."""

    @classmethod
    def final_subcommand(cls) -> abc_app.FinalCommands:
        """Get final subcommand."""
        return abc_app.FinalCommands.INIT

    def __init__(
        self,
        fs_manager: exp_fs.Manager,
        requesting_tool_description: abc_tool_desc.Description,
    ) -> None:
        """Initialize."""
        super().__init__(fs_manager)
        self._requesting_tool_description = requesting_tool_description

    def requesting_tool_description(self) -> abc_tool_desc.Description:
        """Get requesting tool description."""
        return self._requesting_tool_description

    def origin_command(self) -> str:
        """Get original command."""
        return (
            "pbfbench"
            f" {self._requesting_tool_description.topic().cmd()}"
            f" {self._requesting_tool_description.cmd()}"
            f" {self.final_subcommand()}"
            " --help"
        )
