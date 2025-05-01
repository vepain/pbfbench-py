"""Abstract tools results items module."""

from abc import ABC, abstractmethod

import pbfbench.abc.tool.description as abc_tool_desc
import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.items as smp_items
import pbfbench.samples.status as smp_status


class Result(ABC):
    """Result base."""

    def __init__(
        self,
        exp_fs_manager: exp_fs.Manager,
    ) -> None:
        """Initialize."""
        self.__exp_fs_manager = exp_fs_manager

    def exp_fs_manager(self) -> exp_fs.Manager:
        """Get data file system manager."""
        return self.__exp_fs_manager

    @abstractmethod
    def origin_cmd(self) -> str:
        """Get origin command."""
        raise NotImplementedError
        # REFACTOR how to avoid circular import if I want to use abc_tool_app module?
        # To get RunCommand.NAME and InitCommand.NAME e.g. or functions

    @abstractmethod
    def check(self, sample_item: smp_items.Item) -> smp_status.Status:
        """Check input(s)."""
        raise NotImplementedError


class Original(Result):
    """Original result."""

    def origin_cmd(self) -> str:
        """Get origin command."""
        return " ".join(
            [
                "pbfbench",
                self.exp_fs_manager().tool_description().topic().cmd(),
                self.exp_fs_manager().tool_description().cmd(),
                "run",
                "--help",
            ],
        )

    def check(self, sample_item: smp_items.Item) -> smp_status.Status:
        """Check input(s)."""
        sample_fs_manager = self.exp_fs_manager().sample_fs_manager(sample_item)
        return smp_status.get_status(sample_fs_manager)


class Formatted(Result):
    """Formatted result."""

    def __init__(
        self,
        exp_fs_manager: exp_fs.Manager,
        in_need_tool_description: abc_tool_desc.Description,
    ) -> None:
        """Initialize."""
        super().__init__(exp_fs_manager)
        self.__in_need_tool_description = in_need_tool_description

    def in_need_tool_description(self) -> abc_tool_desc.Description:
        """Get in need tool description."""
        return self.__in_need_tool_description

    def origin_cmd(self) -> str:
        """Get origin command."""
        return " ".join(
            [
                "pbfbench",
                self.in_need_tool_description().topic().cmd(),
                self.in_need_tool_description().cmd(),
                "init",
                "--help",
            ],
        )
