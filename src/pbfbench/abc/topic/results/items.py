"""Abstract tools results items module."""

from abc import ABC, abstractmethod

import pbfbench.abc.app as abc_app
import pbfbench.samples.file_system as smp_fs
import pbfbench.samples.status as smp_status


class Result(ABC):
    """Result base."""

    @classmethod
    @abstractmethod
    def check(
        cls,
        sample_fs_manager: smp_fs.Manager,
    ) -> smp_status.Status:
        """Check input(s)."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_final_subcommand(cls) -> abc_app.FinalCommands:
        """Get final subcommand."""
        raise NotImplementedError


class Original(Result):
    """Original result."""

    @classmethod
    def check(
        cls,
        sample_fs_manager: smp_fs.Manager,
    ) -> smp_status.Status:
        """Check input(s)."""
        return smp_status.get_status(sample_fs_manager)

    @classmethod
    def from_final_subcommand(cls) -> abc_app.FinalCommands:
        """Get final subcommand."""
        return abc_app.FinalCommands.RUN


class Formatted(Result):
    """Formatted result."""

    @classmethod
    def from_final_subcommand(cls) -> abc_app.FinalCommands:
        """Get final subcommand."""
        return abc_app.FinalCommands.INIT
