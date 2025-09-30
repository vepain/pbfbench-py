# PlasBin-flow benchmarking framework

## Benchmark file tree structure

The data directory contains cold data (`DATA_DIR`), while the working directory (`WORK_DIR`) acts as a temporary storage for the outputs of running tools (see [core/sbatch_run_process.md](core/sbatch_run_process.md) for more details).
At the end of the runs, the files are moved to the `DATA_DIR` directory, respecting the same structure.

```yaml
DATA_DIR
├── TOPIC_NAME  # e.g. ASSEMBLY
│   └── TOOL_NAME  # e.g. UNICYCLER
│       ├── EXP_NAME  # e.g. default
│       │   ├── SAMPLE_DIRNAME  # e.g. ecol-SAMN10432165
│       │   │   ├── ...  # e.g. Unicycler output files
│       │   │   ├── slurm  # slurm directory
│       │   │   │   ├── command_steps_status.yaml  # Status of each command step (initialization of the environment, command execution, and finalization of the environment)
│       │   │   │   ├── [job_state.{SACCT_STATE}]  # Job state given by the sacct command, see https://slurm.schedmd.com/sacct.html#SECTION_JOB-STATE-CODES
│       │   │   │   ├── [stats.psv]  # File containing the slurm run stats (Pipe Separated Value format) #FIXME what happens if no sacct return value?
│       │   │   │   ├── stdout.log  # Slurm stdout for each sample
│       │   │   │   └── stderr.log  # Slurm stderr for each sample
│       │   │   └── done.log | errors.log | missing_inputs.tsv  # to mark the status of the sample experiment
│       │   ├── ...  # Other samples
│       │   ├── scripts  # Slurm run scripts
│       │   │   ├── YYYY-MM-DD_HH-MM-SS_sbatch.sh  # Main run script sent to sbatch, named according to the horodatage
│       │   │   ├── YYYY-MM-DD_HH-MM-SS_init_env.sh  # Sub run script corresponding to the initialization of the environment
│       │   │   ├── YYYY-MM-DD_HH-MM-SS_command.sh  # Sub run script corresponding to the execution of the command
│       │   │   └── YYYY-MM-DD_HH-MM-SS_close_env.sh  # Sub run script corresponding to the finalization of the environment
│       │   ├── config.yaml  # Configurations of the experiment on the tool for the topic
│       │   ├── [in_progress.yaml]  # YAML file containing the run in progress (linked to the working directory)
│       │   ├── [history.yaml]  # YAML file containing history of runs
│       │   └── [errors.tsv]  # Lists of samples with error (missing inputs or error during slurm run)
│       └── env_wrapper.sh  # Tool environment wrapper script (only in DATA_DIR tree)
└── samples.tsv  # Only in DATA_DIR
```

## Python program to launch experiments

A typical call to the command is:
<!-- DOCU fix command args order -->
<!-- DOCU add run target options -->
```sh
pbfbench topic-cmd tool-cmd run $EXP_NAME $DATA_DIR $WORK_DIR $EXP_CFG_YAML [--slurm-config $SLURM_CFG_STRING]
```

where:

* sub-commands:
  * `topic-cmd` is the command associated to the topic (e.g. `assembly` for assembly)
  * `tool-cmd` is the command associated to the tool (e.g. `unicycler` for Unicycler)

### Arguments

* `EXP_NAME` is the name of the experiment
* `DATA_DIR` is the **absolute** path to the data directory
* `WORK_DIR` is the **absolute** path to the working directory
* `EXP_CFG_YAML` is the **absolute** path to the experiment configuration File

### Options

* `--slurm-config` is the slurm configuration string, e.g. `--slurm-config "--mem=36"` (can also point to a file that contains the string)  <!-- FEATURE Read file for slurm configs -->

## Tool environment wrapper script

For each topic, each tool is associated with an environment wrapper script in `DATA_DIR/TOPIC_NAME/TOOL_NAME/env_wrapper.sh`.

See [environments/README.md](environments/README.md) for more details.

<!-- DOCU explain how to properly set the environment according to the tool command template (with command for help) -->

## Experiment

The `DATA_DIR/TOPIC_NAME/TOOL_NAME/EXP_NAME` directory contains the result of an experiment.

### Configuration

The `config.yaml` file contains the configuration for the experiment.

For a given topic `TOPIC_NAME` and tool `TOOL_NAME`, a draft of a configuration file `$exp_cfg_yaml` can be obtained with:

```sh
pbfbench topic-cmd tool-cmd config $exp_cfg_yaml
```

> [!Tip]
> The `topic-cmd` and `tool-cmd` are the kebab-case versions of respectively `TOPIC_NAME` and `TOOL_NAME`.
>
> In general, use `pbfbench --help` and `pbfbench topic-cmd --help` to get the valid commands.

The structure is defined bellow, and the examples are for a binning tool:

```yaml
arguments:  # tool arguments
  ARGUMENT_NAME:  # e.g. GENOME
    - TOOL_NAME  # e.g. UNICYCLER
    - EXP_NAME  # e.g. default
  ...
options:  # tool options
  - "--long-option value"  # e.g. "--min-length=1000"
    ...
```

Example for producing seeds with Platon:

```sh
EXP_NAME=my_first_experiment
DATA_DIR=/home/camille/pbfbench/data
WORK_DIR=/home/camille/pbfbench/work
EXP_CFG_YAML=/home/camille/pbfbench/configs/configs.yaml

pbfbench seeds platon run $EXP_NAME $DATA_DIR $WORK_DIR $EXP_CFG_YAML
```

<!-- FIXME be sure to remove tool key and up its content -->

```yaml
arguments:  # Platon arguments
  GENOME:  # Name of the argument given by Platon's DOCU
    - UNICYCLER  # Name of a tool providing a gunzip FASTA file
    - default  # Unicycler experiment name
options:  # Platon options
  - "--db \"/absolute/path/to/platon/db\""  # Escape quotes because of YAML
```

### Slurm configuration

The SLURM configuration file is optional.

You can obtain the default configuration with:

```sh
pbfbench slurm-opts [ACCOUNT_NAME] > slurm_cfg.sh
```

Where `slurm_cfg.sh` contains:

```sh
> echo $( cat slurm_opts.sh )
--mem=4096 --cpus-per-task=4 --time=1:00:00 --account=ACCOUNT_NAME
```

### Outputs

Each sample is associated to a directory names `SAMPLE_DIRNAME=${species_id}_${sample_id}` in the experiment directory.

#### Errors report

The `EXP_NAME/errors.tsv` file contains the list of samples with missing inputs or error during the slurm execution:

```python
sample_id            reason
ecol_SAMN10432165    missing_inputs
... # other missing inputs
abau_SAMN10432164    error
... # other errors
```

The reason is one of the following:

* `missing_inputs` if at least one of the inputs of the input is missing
* `error` if the input experiment returned an error

#### Sample outputs

The benchmark manager `pbfbench` communicates the end of an experiment in each sample directory `SAMPLE_DIRNAME` with a system of files:

* If at least one input is missing (see later for missing reasons):
  * `missing_inputs.tsv` lists the missing inputs and their reasons
* Otherwise:
  * If one thing fails during the slurm script execution: `errors.log` contains the error messages (copy content of slurm error log)
  * Otherwise: `done.log` is created (copy content of slurm stdout log)

The `slurm` directory contains supplementary information about the slurm job processes.

##### Missing inputs list

The `EXP_NAME/SAMPLE_DIRNAME/missing_inputs.tsv` file contains the missing inputs for each sample:

```html
arg_name    input_topic    input_tool    input_experiment    reason    help
GENOME      ASSEMBLY       UNICYCLER     default             not_run   "pbfbench asm unicycler run --help"
```

The reason is one of the following:

* `not_run` if the input experiment was not run or did not produce logs
* `missing_inputs` if at least one of the inputs of the input is missing
* `error` if the input experiment returned an error

The help column provides a potential solution.

##### Slurm logs

The `slurm` directory under `EXP_NAME/SAMPLE_DIRNAME` contains the slurm logs for that samples:

* `command_steps_status.yaml` Status of each command step (initialization of the environment, command execution, and finalization of the environment)

  ```yaml
  init_env: <COMMAND_STATUS>
  command: <COMMAND_STATUS>
  close_env: <COMMAND_STATUS>
  ```

  where `<COMMAND_STATUS>` is one of the following:

  * `OK` if the step succeeded
  * `ERROR` if the step failed
  * `NULL` if the step did not return any state (yet)

  If one of the step status is `None`, the `sbatch` job state file `job_state.{SACCT_STATE}` can explain the reason why the step does not return any status (e.g. because of Slurm time limit reached).

* `job_state.{SACCT_STATE}` Job state given by the `sacct` command, if `sacct` returned something. See possible states in <https://slurm.schedmd.com/sacct.html#SECTION_JOB-STATE-CODES>
* `stats.psv` File containing the slurm run stats (Pipe Separated Value format, can be empty depending on `sacct` output)
* `stdout.log` Slurm stdout for that sample
* `stderr.log` Slurm stderr for that sample

#### Run in progress YAML file

<!-- TODO DATA_DIR/../in_progress.yaml file logic -->

The `EXP_NAME/in_progress.yaml` file contains the working experiment in progress:

```yaml
date: 2025-09-16
working_directory: /path/to/WORK_DIR
job_id: <str>
```

> [!NOTE]
> The `DATA_DIR/.../EXP_NAME/in_progress.yaml` file contains the working directory path while the `WORK_DIR/.../EXP_NAME/in_progress.yaml` file contains the data directory path.

#### Run history YAML file

<!-- TODO history.yaml file logic -->

The `EXP_NAME/history.yaml` file containing the history of the runs (as a list):

```yaml
- date: 2025-09-16
  job_id: <str or None>
  stats:
    total_number_of_samples: <int> # Total = NSS + NSMI + NFS + NSNR
    number_of_successfull_samples: <int>  # NSS
    number_of_samples_with_missing_input: <int>  # NSMI
    number_of_failed_samples: <int>  # NFS
    number_of_not_run_samples: <int>  # NSNR No missing inputs but cannot assess if it failed or not
```

### Internal process

The documentation [core/sbatch_run_process.md](core/sbatch_run_process.md) describes the internal process of the `sbatch` run process, and how `pbfbench` manages a job when it finishes
