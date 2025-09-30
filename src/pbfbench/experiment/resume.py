"""Resume experiment."""

from __future__ import annotations

from . import managers, monitors, resolve


def resume(
    exp_manager: managers.OnlyOptions | managers.WithArguments,
    array_job_id: str,
) -> None:
    """Resume experiment."""
    unresolved_samples = list(
        monitors.iter_unresolved_samples(exp_manager.work_fs_manager()),
    )
    resolve.resolve_running_samples(exp_manager, unresolved_samples, array_job_id)
