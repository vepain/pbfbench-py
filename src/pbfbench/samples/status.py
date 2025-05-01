"""Sample experiment status logics module."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pbfbench.samples.file_system as smp_fs


class OKStatus(StrEnum):
    """Sample experiment OK status."""

    OK = "ok"


class ErrorStatus(StrEnum):
    """Sample experiment error status."""

    # The sample experiment has never been run or exit before log
    NOT_RUN = "not_run"
    # One of the input is missing
    MISSING_INPUTS = "missing_inputs"
    # An error occur during the sample experiment run
    ERROR = "error"


type Status = OKStatus | ErrorStatus


def get_status(sample_fs_manager: smp_fs.Manager) -> Status:
    """Get sample experiment status."""
    if not sample_fs_manager.sample_dir().exists():
        return ErrorStatus.NOT_RUN
    if sample_fs_manager.missing_inputs_tsv().exists():
        return ErrorStatus.MISSING_INPUTS
    if sample_fs_manager.errors_log().exists():
        return ErrorStatus.ERROR
    if sample_fs_manager.done_log().exists():
        return OKStatus.OK
    return ErrorStatus.NOT_RUN
