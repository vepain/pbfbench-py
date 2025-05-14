"""Abstract tools results items module."""

from abc import ABC, abstractmethod

import pbfbench.experiment.file_system as exp_fs
import pbfbench.samples.items as smp_items
import pbfbench.samples.status as smp_status


class Result(ABC):
    """Result base."""

    def __init__(self, exp_fs_manager: exp_fs.ManagerBase) -> None:
        """Initialize."""
        self._exp_fs_manager = exp_fs_manager

    def exp_fs_manager(self) -> exp_fs.ManagerBase:
        """Get file system manager."""
        return self._exp_fs_manager

    # REFACTOR not sure it is relevant to use sample status, because of formatted
    @abstractmethod
    def check(self, sample_item: smp_items.Item) -> smp_status.Status:
        """Check input(s)."""
        raise NotImplementedError


class Original(Result):
    """Original result."""

    def check(self, sample_item: smp_items.Item) -> smp_status.Status:
        """Check input(s)."""
        return smp_status.get_status(
            self._exp_fs_manager.sample_fs_manager(sample_item),
        )


class Formatted(Result):
    """Formatted result."""
