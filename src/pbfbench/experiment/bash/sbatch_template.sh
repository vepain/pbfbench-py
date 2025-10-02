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
    echo "${SLURM_ARRAY_JOB_ID}" >"${ARRAY_JOB_ID_FILE}"
fi

# ------------------------------------------------------------------------------------ #
# Step status functions
# ------------------------------------------------------------------------------------ #
set -e # Exit at the first command failing

function log_step_ok {
    local TMP_STATUS_FILE=${1}
    touch "${TMP_STATUS_FILE}"
}
function exit_step_error {
    local TMP_STATUS_FILE=${1}
    touch "${TMP_STATUS_FILE}"
    exit 1
}

# ------------------------------------------------------------------------------------ #
# Initialize the tool environment
# ------------------------------------------------------------------------------------ #
# PBFBENCH_DO:STEP:INIT_ENV

trap 'exit_step_error "${INIT_ENV_STEP_ERROR_FILE}"' ERR
# shellcheck source=/dev/null
source "${INIT_ENV_SCRIPT}"
log_step_ok "${INIT_ENV_STEP_OK_FILE}"

# ------------------------------------------------------------------------------------ #
# Run the tool
# ------------------------------------------------------------------------------------ #
# PBFBENCH_DO:STEP:COMMAND

srun "${COMMAND_SCRIPT}" || exit_step_error "${COMMAND_STEP_ERROR_FILE}"
log_step_ok "${COMMAND_STEP_OK_FILE}"

# ------------------------------------------------------------------------------------ #
# Close the tool environment
# ------------------------------------------------------------------------------------ #
# PBFBENCH_DO:STEP:CLOSE_ENV

trap 'exit_step_error "${CLOSE_ENV_STEP_ERROR_FILE}"' ERR
# shellcheck source=/dev/null
source "${CLOSE_ENV_SCRIPT}"
log_step_ok "${CLOSE_ENV_STEP_OK_FILE}"
