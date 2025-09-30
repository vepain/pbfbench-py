"""Experiment bash steps."""

from enum import StrEnum


class PbfbenchDo(StrEnum):
    """Experiment bash steps."""

    SBATCH_COMMENTS = "SBATCH_COMMENTS"
    ARRAY_JOB_ID_FILE = "ARRAY_JOB_ID_FILE"
    STEP = "STEP"


class Steps(StrEnum):
    """Experiment bash steps."""

    INIT_ENV = "INIT_ENV"
    COMMAND = "COMMAND"
    CLOSE_ENV = "CLOSE_ENV"
