"""Experiment slurm status."""

from enum import StrEnum


class ScriptSteps(StrEnum):
    """Command step status."""

    OK = "OK"
    ERROR = "ERROR"
    NULL = "NULL"
