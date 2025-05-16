#!/usr/bin/env bash
# ------------------------------------------------------------------------------------ #
# sbatch comments
# ------------------------------------------------------------------------------------ #
# PBFBENCH_DO:SBATCH_COMMENTS

# ------------------------------------------------------------------------------------ #
# Write array job id in file
# ------------------------------------------------------------------------------------ #
# PBFBENCH_DO:ARRAY_JOB_ID_FILE

if [[ ! -f ${ARRAY_JOB_ID_FILE} ]]; then
    echo "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}" >"${ARRAY_JOB_ID_FILE}"
fi

# ------------------------------------------------------------------------------------ #
# Step status functions
# ------------------------------------------------------------------------------------ #
function log_step_ok {
    local TMP_STATUS_FILE=${1}
    touch ${TMP_STATUS_FILE}
}
function exit_step_error {
    local TMP_STATUS_FILE=${1}
    touch ${TMP_STATUS_FILE}
    exit 1
}

# ------------------------------------------------------------------------------------ #
# Initialize the tool environment
# ------------------------------------------------------------------------------------ #
# PBFBENCH_DO:STEP:INIT_ENV

bash -e ${INIT_ENV_SCRIPT} || exit_step_error ${INIT_ENV_STEP_ERROR_FILE}
log_step_ok ${INIT_ENV_STEP_OK_FILE}

# ------------------------------------------------------------------------------------ #
# Run the tool
# ------------------------------------------------------------------------------------ #
# PBFBENCH_DO:STEP:COMMAND

srun ${COMMAND_SCRIPT} || exit_step_error ${COMMAND_STEP_ERROR_FILE}
log_step_ok ${COMMAND_STEP_OK_FILE}

# ------------------------------------------------------------------------------------ #
# Close the tool environment
# ------------------------------------------------------------------------------------ #
# PBFBENCH_DO:STEP:CLOSE_ENV

bash -e ${CLOSE_ENV_SCRIPT} || exit_step_error ${CLOSE_ENV_STEP_ERROR_FILE}
log_step_ok ${CLOSE_ENV_STEP_OK_FILE}
