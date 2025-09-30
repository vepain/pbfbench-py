# How pbfbench manages SLURM jobs?

The manager `pbfbench` writes into the working directory during the experiment sample processing.
In the process, the `EXP_NAME/logs` temporarily directory contains the sbatch log files.

When one sample experiment finishes, `pbfbench` arranges its logs into the sample experiment directory (`EXP_NAME/SAMPLE_DIRNAME`).
`pbfbench` decides whether the sample experiment succeeded or failed based on the state return of the `sacct` command, otherwise thanks to the command steps status files (`logs/%A_%a_init_env.{ok|error}`, `logs/%A_%a_command.{ok|error}` and `logs/%A_%a_close_env.{ok|error}`).

```yaml
WORK_DIR
└── TOPIC_NAME  # e.g. ASSEMBLY
    └── TOOL_NAME  # e.g. UNICYCLER
        └── EXP_NAME  # e.g. default
            ├── SAMPLE_DIRNAME  # e.g. ecol-SAMN10432165
            │   └── ...  # e.g. Unicycler output files
            ├── ...  # Other samples
            ├── logs  # Temporary logs directory, created before the sbatch run, deleted at the end of pbfbench run
            │   ├── array_job.id  # Temporarily file that contains sbatch array job id
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
            ├── config.yaml  # Configurations of the experiment on the tool for the topic
            ├── [in_progress.yaml]  # YAML file containing the run in progress (linked to the data directory)
            ├── resolved_samples.tsv  # TSV file monitoring which samples have been already resolved  # TODO resolved_samples.tsv
            └── unresolved_samples.tsv  # TSV file monitoring which samples have not been yet resolved # TODO[2025-09-16] Sample status monitoring in exp work dir (usefull for resume purpose)
```

There are two type of commands:

* The [`run` command](#run-process) `pbfbench topic-cmd tool-cmd run $EXP_NAME $DATA_DIR $WORK_DIR $CONFIG_YAML ...`
* The [`resume` command](#resume-the-experiment) `pbfbench topic-cmd tool-cmd resume $EXP_NAME $DATA_DIR`

## Run process

When the `run` subcommand is called:

1. Check the read/write permissions and the configuration file validity
2. Check if the experiment is already running (thanks to the `DATA_DIR/.../EXP_NAME/in_progress.yaml` file, whether the working directory path was the same or is different for the one given at the moment of the call)
    * Yes: exit with error (message to say to use the `resume` command)
    * No: [start the new experiment](#start-the-new-experiment)

### Start the new experiment

1. Create or reset (if exists) experiment working directory
2. Check if the experiment has to be completed (by checking existence of the `DATA_DIR/.../EXP_NAME/config.yaml` file)
    * Yes: verify the configuration file are the same
        * No: exit with error to say that configurations differ
    * No: copy the configuration file to `DATA_DIR/.../EXP_NAME/config.yaml` and in `WORK_DIR/.../EXP_NAME/config.yaml` to keep a trace and for further checks
3. Get the list of samples to run (according to the options), and:
    * Remove the sample lines from `DATA_DIR/.../errors.tsv` if it corresponds to a sample to run
    * Add the sample lines to the new `unresolved_samples.tsv` file
4. If inputs are required:
    1. given a sample in the list of samples to run, format it if required
        * log critical error if there is at least one of its argument for which the formatting fails
    2. given a sample in the list of samples to run (even with formatting fail), if there is a missing input:
        1. reset data sample directory and write the list of missing inputs in `DATA_DIR/.../SAMPLE_DIRNAME/missing_inputs.tsv`
        2. write missing inputs in `DATA_DIR/.../errors.tsv` file
        3. remove the concerning samples from the list of samples to run and update files `resolved_samples.tsv` and `unresolved_samples.tsv`
5. Create `scripts` directories (both in `DATA_DIR/.../EXP_NAME` and in `WORK_DIR/.../EXP_NAME`) and write the scripts in them.
6. Launch the SLURM jobs associated with the samples to run
    * If error: write new history event, exit with critical error
    * Extract the job ID and remove the temporary array job ID file `logs/array_job.id`
7. Write the in-progress experiment metadata files:
    * `DATA_DIR/.../EXP_NAME/in_progress.yaml`
    * `WORK_DIR/.../EXP_NAME/in_progress.yaml`
8. [Resolve the sample jobs](#resolve-the-sample-jobs)

## Resume the experiment
<!-- TODO[2025-09-30 11:38:08] CONTINUE HERE -->
1. Check if the experiment is running (by checking existence of the `DATA_DIR/.../EXP_NAME/in_progress.yaml` file)
    * No: exit with warning (message to say already resolved)
2. Get the list of unresolved samples (thanks to the `unresolved_samples.tsv` file)
3. [Resolve the samples](#resolve-the-sample-jobs) (wait them to success, fail or disappear from `sacct` monitoring)

## Resolve the sample jobs

`sbatch` job creates for each sample (not managed by `pbfbench` Python part):

1. The sample directory `EXP_NAME/SAMPLE_DIRNAME` <!-- DOCU Where do I create sample dir? seems to depend on the tool script -->
2. Create and complete the `logs/%A_%a_...` files

In parallel, `pbfbench` loops on the list of unresolved samples until this list is empty:

1. Check the status of the samples:
    * `sacct` returns a state:
        * Success: return success status
        * Error: return error status
        * Other: return not run status, keep in the unresolved samples list
    * `sacct` does not return a state:
        * If closing environment is a success (file `%A_%a_close_env.ok` exists): return success status
        * Else: return error status
2. [Manage the new resolved samples](#manage-the-new-resolved-samples)
3. Loop until all samples are resolved, then [clean the working experiment directory](#clean-the-working-experiment-directory)

### Manage the new resolved samples

Once the sample job finishes, sample status files are created and the corresponding slurm log files are moved to the sample directory and renamed:

1. Manage specificities of OK resolved samples:
    1. Copy the content of `logs/%A_%a_stdout.log` to `SAMPLE_DIRNAME/done.log`
2. Manage specificities of error resolved samples:
    1. Copy the content of `logs/%A_%a_stderr.log` to `SAMPLE_DIRNAME/errors.log`
    2. Add their line to the `errors.tsv` file
3. For all the resolved samples:
    1. Create `SAMPLE_DIRNAME/slurm/job_state.{SACCT_STATE}` file (exists only if there is a `sacct`)
    2. Create `SAMPLE_DIRNAME/slurm/stats.psv` file (if `sacct` returns a state) <!-- DOCU can only contain the header if job ID not found by sacct  -->
    3. Copy the content of `logs/%A_%a_stdout.log` to `SAMPLE_DIRNAME/slurm/stdout.log`
    4. Copy the content of `logs/%A_%a_stderr.log` to `SAMPLE_DIRNAME/slurm/stderr.log`
    5. Transform `logs/%A_%a_init_env.{ok|error}`, `logs/%A_%a_command.{ok|error}` and `logs/%A_%a_close_env.{ok|error}` -> `SAMPLE_DIRNAME/slurm/command_steps_status.yaml`
    6. Remove `DATA_DIR/.../SAMPLE_DIRNAME` (if exists) and move `WORK_DIR/.../SAMPLE_DIRNAME` to `DATA_DIR/.../SAMPLE_DIRNAME`.
    7. Remove the resolved sample from `unresolved_samples.tsv` file and add it with its status in the `resolved_samples.tsv` file

### Clean the working experiment directory

When all the samples finish:

1. Add the new complete experiment entry to `DATA_DIR/.../EXP_NAME/history.yaml`
2. Remove the whole `WORK_DIR/.../EXP_NAME` directory and try to remove empty parent directories

## File formats

### Run in progress YAML file

<!-- TODO WORK_DIR/../in_progress.yaml file logic -->

The `EXP_NAME/in_progress.yaml` file details the working experiment metadata

```yaml
date: 2025-09-16
data_directory: /path/to/DATA_DIR
job_id: <str>
```

> [!NOTE]
> The `DATA_DIR/.../EXP_NAME/in_progress.yaml` file contains the working directory path while the `WORK_DIR/.../EXP_NAME/in_progress.yaml` file contains the data directory path.

### Monitor files `unresolved_samples.tsv` and `resolved_samples.tsv`

File `unresolved_samples.tsv` keep trace of samples not yet resolved:

```html
row_number  species_id  sample_id
<int>       <str>       <str>
...
```

File `resolved_samples.tsv` gives the status of resolved sample.

```html

exp_sample_id       status
<SAMPLE_DIRNAME>    <samples.status.Status>
...
```
