"""Sample experiment status logics module."""

from __future__ import annotations

from contextlib import suppress
from enum import StrEnum
from typing import TYPE_CHECKING, Self, assert_never

from pbfbench.slurm import sacct

if TYPE_CHECKING:
    import pbfbench.samples.file_system as smp_fs


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


class StatusMap[T]:
    """Status map."""

    @classmethod
    def default(cls, default_value: T) -> Self:
        """Get default status map."""
        return cls(default_value, default_value, default_value, default_value)

    def __init__(self, ok: T, missing_inputs: T, error: T, not_run: T) -> None:
        self._ok = ok
        self._missing_inputs = missing_inputs
        self._error = error
        self._not_run = not_run

    def get(self, status: Status) -> T:
        """Get status map value."""
        match status:
            case OK.OK:
                return self._ok
            case Error.MISSING_INPUTS:
                return self._missing_inputs
            case Error.ERROR:
                return self._error
            case Error.NOT_RUN:
                return self._not_run

    def set(self, status: Status, value: T) -> None:
        """Set status map value."""
        match status:
            case OK.OK:
                self._ok = value
            case Error.MISSING_INPUTS:
                self._missing_inputs = value
            case Error.ERROR:
                self._error = value
            case Error.NOT_RUN:
                self._not_run = value
            case _:
                assert_never(status)

    def __getitem__(self, status: Status) -> T:
        """Get status map value."""
        return self.get(status)

    def __setitem__(self, status: Status, value: T) -> None:
        """Set status map value."""
        self.set(status, value)


def status_from_str(status_str: str) -> Status:
    """Get sample experiment status from string."""
    with suppress(ValueError):
        return Error(status_str)
    return OK(status_str)


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
