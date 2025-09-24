"""Experiment SLURM step checking module."""

import pbfbench.experiment.bash.items as exp_bash_items
import pbfbench.experiment.file_system as exp_fs
import pbfbench.experiment.slurm.status as exp_slurm_status


def script_step_status(
    work_exp_fs_manager: exp_fs.WorkManager,
    job_id: str,
    step: exp_bash_items.Steps,
) -> exp_slurm_status.ScriptSteps:
    """Get SLURM script step status thanks to the experiment file system."""
    ok_file = work_exp_fs_manager.slurm_log_fs_manager().script_step_status_file(
        job_id,
        step,
        exp_slurm_status.ScriptSteps.OK,
    )
    error_file = work_exp_fs_manager.slurm_log_fs_manager().script_step_status_file(
        job_id,
        step,
        exp_slurm_status.ScriptSteps.ERROR,
    )
    if ok_file.exists():
        status = exp_slurm_status.ScriptSteps.OK
    elif error_file.exists():
        status = exp_slurm_status.ScriptSteps.ERROR
    else:
        status = exp_slurm_status.ScriptSteps.NULL
    ok_file.unlink(missing_ok=True)
    error_file.unlink(missing_ok=True)
    return status
