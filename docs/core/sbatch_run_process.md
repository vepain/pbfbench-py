# How pbfbench manages sbatch jobs?

The manager `pbfbench` writes into the working directory during the experiment sample processing.
In the process, the `$exp_name/logs` temporarily directory contains the sbatch log files.

When one sample experiment finishes, `pbfbench` arrange its logs into the sample experiment directory (`$exp_name/$SAMPLE_DIRNAME`).
`pbfbench` decides whether the sample experiment succeeded or failed based on the state return of the `sacct` command, otherwise thanks to the command steps status files (`logs/%A_%a_init_env.{ok|error}`, `logs/%A_%a_command.{ok|error}` and `logs/%A_%a_close_env.{ok|error}`).

```yaml
WORK_DIR
└── $TOPIC_NAME  # e.g. ASSEMBLY
    └── $TOOL_NAME  # e.g. UNICYCLER
        └── $exp_name  # e.g. default
            ├── $SAMPLE_DIRNAME  # e.g. ecol-SAMN10432165
            │   └── ...  # e.g. Unicycler output files
            ├── ...  # Other samples
            ├── logs  # Temporary logs directory, created before the sbatch run, deleted at the end of pbfbench run
            │   ├── array_job.id  # File containing the array job id (%A), deleted at the end of sbatch runs
            │   ├── %A_%a_stdout.log  # Slurm stdout for each sample
            │   ├── %A_%a_stderr.log  # Slurm stderr for each sample
            │   ├── [%A_%a_init_env.{ok|error}]  # Command step empty log file for initialization of the environment
            │   ├── [%A_%a_command.{ok|error}]  # Command step empty log file for command execution
            │   └── [%A_%a_close_env.{ok|error}]  # Command step empty log file for finalization of the environment
            ├── scripts  # Slurm run scripts
            │   ├── YYYY-MM-DD_HH-MM-SS_sbatch.sh  # Main run script sent to sbatch, named according to the horodatage
            │   ├── YYYY-MM-DD_HH-MM-SS_init_env.sh  # Sub run script corresponding to the initialization of the environment
            │   ├── YYYY-MM-DD_HH-MM-SS_command.sh  # Sub run script corresponding to the execution of the command
            │   └── YYYY-MM-DD_HH-MM-SS_close_env.sh  # Sub run script corresponding to the finalization of the environment
            ├── date.txt  # File containing the string corresponding to the last experiment date
            └── config.yaml  # Configurations of the experiment on the tool for the topic
```

Once the sample job finishes, sample status files are created and the corresponding slurm log files are moved to the sample directory and renamed:

* Create `$SAMPLE_DIRNAME/done.log` or `$SAMPLE_DIRNAME/errors.log` files according to the status determined by `sacct` or by the command steps status if `sacct` did not return any state for the job
* Create `$SAMPLE_DIRNAME/slurm/job_state.{SACCT_STATE}` file (can be empty depending of `sacct` output)
* Create `$SAMPLE_DIRNAME/slurm/stats.psv` file
* `logs/%A_%a_stdout.log` -> `$SAMPLE_DIRNAME/slurm/stdout.log`
* `logs/%A_%a_stderr.log` -> `$SAMPLE_DIRNAME/slurm/stderr.log`
* `logs/%A_%a_init_env.{ok|error}`, `logs/%A_%a_command.{ok|error}` and `logs/%A_%a_close_env.{ok|error}` -> `$SAMPLE_DIRNAME/slurm/command_steps_status.yaml`

The `WORK_DIR/.../$SAMPLE_DIRNAME` is then moved to the `DATA_DIR/.../$SAMPLE_DIRNAME`.

When all the samples finish, the temporary `logs/array_job.id` file is deleted, and the `logs` directory is deleted (if empty).
