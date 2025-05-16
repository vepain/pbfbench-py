"""Sample experiment status logics module."""

from __future__ import annotations

from enum import StrEnum

import pbfbench.samples.file_system as smp_fs
import pbfbench.slurm.status as slurm_status


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


def from_sacct_state(
    status: slurm_status.SACCTState,
) -> Status:
    """Get sample experiment status from sacct state."""
    match status:
        case (
            slurm_status.SACCTState.BOOT_FAIL
            | slurm_status.SACCTState.CANCELLED
            | slurm_status.SACCTState.DEADLINE
            | slurm_status.SACCTState.FAILED
            | slurm_status.SACCTState.NODE_FAIL
            | slurm_status.SACCTState.OUT_OF_MEMORY
            | slurm_status.SACCTState.REVOKED
            | slurm_status.SACCTState.TIMEOUT
        ):
            return ErrorStatus.ERROR
        case slurm_status.SACCTState.COMPLETED:
            return OKStatus.OK
        case (
            slurm_status.SACCTState.PENDING
            | slurm_status.SACCTState.PREEMPTED
            | slurm_status.SACCTState.RUNNING
            | slurm_status.SACCTState.REQUEUED
            | slurm_status.SACCTState.RESIZING
            | slurm_status.SACCTState.SUSPENDED
        ):
            return ErrorStatus.NOT_RUN
