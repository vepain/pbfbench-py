"""Sample experiment status logics module."""

from __future__ import annotations

from enum import StrEnum

import pbfbench.samples.file_system as smp_fs
from pbfbench.slurm import sacct


class OK(StrEnum):
    """Sample experiment OK status."""

    OK = "ok"


class Error(StrEnum):
    """Sample experiment error status."""

    # The sample experiment has never been run or exit before log
    NOT_RUN = "not_run"
    # One of the input is missing
    MISSING_INPUTS = "missing_inputs"
    # An error occur during the sample experiment run or sacct state is unknown
    ERROR = "error"


type Status = OK | Error


def get_status(sample_fs_manager: smp_fs.Manager) -> Status:
    """Get sample experiment status."""
    if not sample_fs_manager.sample_dir().exists():
        return Error.NOT_RUN
    if sample_fs_manager.missing_inputs_tsv().exists():
        return Error.MISSING_INPUTS
    if sample_fs_manager.errors_log().exists():
        return Error.ERROR
    if sample_fs_manager.done_log().exists():
        return OK.OK
    return Error.NOT_RUN


def from_sacct_state(status: sacct.State) -> Status:
    """Get sample experiment status from sacct state."""
    match status:
        case (
            sacct.State.BOOT_FAIL
            | sacct.State.CANCELLED
            | sacct.State.DEADLINE
            | sacct.State.FAILED
            | sacct.State.NODE_FAIL
            | sacct.State.OUT_OF_MEMORY
            | sacct.State.REVOKED
            | sacct.State.TIMEOUT
        ):
            return Error.ERROR
        case sacct.State.COMPLETED:
            return OK.OK
        case (
            sacct.State.PENDING
            | sacct.State.PREEMPTED
            | sacct.State.RUNNING
            | sacct.State.REQUEUED
            | sacct.State.RESIZING
            | sacct.State.SUSPENDED
        ):
            return Error.NOT_RUN
