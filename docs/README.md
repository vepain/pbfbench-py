# PlasBin-flow benchmarking framework

## Benchmark file tree structure

The data directory contains cold data (`DATA_DIR`), while the working directory (`WORK_DIR`) acts as a temporary storage for the outputs of running tools (see [core/sbatch_run_process.md](core/sbatch_run_process.md) for more details).
At the end of the runs, the files are moved to the `DATA_DIR` directory, respecting the same structure.

```yaml
DATA_DIR
├── $TOPIC_NAME  # e.g. ASSEMBLY
│   └── $TOOL_NAME  # e.g. UNICYCLER
│       ├── $exp_name  # e.g. default
│       │   ├── $SAMPLE_DIRNAME  # e.g. ecol-SAMN10432165
│       │   │   ├── ...  # e.g. Unicycler output files
│       │   │   ├── slurm  # slurm directory
│       │   │   │   ├── command_steps_status.yaml  # Status of each command step (initialization of the environment, command execution, and finalization of the environment)
│       │   │   │   ├── [job_state.{SACCT_STATE}]  # Job state given by the sacct command, see https://slurm.schedmd.com/sacct.html#SECTION_JOB-STATE-CODES
│       │   │   │   ├── stats.psv  # File containing the slurm run stats (Pipe Separated Value format)
│       │   │   │   ├── stdout.log  # Slurm stdout for each sample
│       │   │   │   └── stderr.log  # Slurm stderr for each sample
│       │   │   └── done.log | errors.log | missing_inputs.tsv  # to mark the status of the sample experiment
│       │   ├── ...  # Other samples
│       │   ├── scripts  # Slurm run scripts
│       │   │   ├── YYYY-MM-DD_HH-MM-SS_sbatch.sh  # Slurm run script according to the horodatage
│       │   │   └── YYYY-MM-DD_HH-MM-SS_command.sh  # srun commands without init and close tool environment processes
│       │   ├── config.yaml  # Configurations of the experiment on the tool for the topic
│       │   ├── date.txt  # File containing the string corresponding to the last experiment date
│       │   └── [errors.tsv]  # Lists of samples with error (missing inputs or error during slurm run)
│       └── env_wrapper.sh  # Tool environment wrapper script (only in DATA_DIR tree)
└── samples.tsv  # Only in DATA_DIR
```

## Python program to launch experiments

A typical call to the command is:
<!-- DOCU fix command args order -->
```sh
pbfbench $topic_cmd $tool_cmd run $data_dir $work_dir $exp_cfg_yaml [--rerun]
```

The command is composed of:

* sub-commands:
  * `topic_cmd` is the command associated to the topic (e.g. `asm` for assembly)
  * `tool_cmd` is the command associated to the tool (e.g. `unicycler` for Unicycler)
* arguments:
  * `data_dir` is the **absolute** path to the data directory
  * `work_dir` is the **absolute** path to the working directory
  * `exp_cfg_yaml` is the **absolute** path to the experiment configuration File

## Tool environment wrapper script

For each topic, each tool is associated with an environment wrapper script in `$TOPIC/$TOOL/env_wrapper.sh`.

See [environments/README.md](environments/README.md) for more details.

<!-- DOCU explain how to properly set the environment according to the tool command template (with command for help) -->

## Experiment

The `config.yaml` file contains the configuration for the experiment.
The structure is defined bellow, and the examples are for a binning tool:

```yaml
name: $exp_name  # e.g. MinLen1000
tool:
  arguments:  # tool arguments
    $topic_name:  # e.g. ASSEMBLY
      - $tool_name  # e.g. UNICYCLER
      - $exp_name  # e.g. default
    ...
  options:  # tool options
    # Sub YAML structure when the tool uses a YAML config file for the options
    # e.g.
    # min_length: 1000
    # OR
    - "--long-option value"  # e.g. "--min-length=1000"
    ...
slurm:
  - "--mem=36"
  - "--cpus-per-task=16"
  ...  # all but options for array jobs and logs which are automatically set
```

Example for producing seeds with Platon:

```sh
pbfbench seeds platon run $data_dir $work_dir $exp_cfg_yaml [--rerun]
```

```yaml
name: default
tool:
  arguments:  # Platon arguments
    GENOME:  # Name of the argument given by Platon's DOCU
      - UNICYCLER  # Name of a tool providing a gunzip FASTA file
      - default  # Unicycler experiment name
  options:  # Platon options
    - "--db \"/absolute/path/to/platon/db\""  # Escape quotes because of YAML
slurm:
  - "--mem=36"
  - "--cpus-per-task=16"
  ...  # all but options for array jobs and logs which are automatically set
```

### Experiment outputs

Each sample is associated to a directory names `SAMPLE_DIRNAME=${species_id}_${sample_id}` in the experiment directory.

The `$exp_name/errors.tsv` file contains the list of samples with missing inputs or error during the slurm execution:

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

### Sample outputs

The benchmark manager `pbfbench` communicates the end of an experiment in each sample directory `$SAMPLE_DIRNAME` with a system of files:

* If at least one input is missing (see later for missing reasons):
  * `missing_inputs.tsv` lists the missing inputs and their reasons
* Otherwise:
  * If one thing fails during the slurm script execution: `errors.log` contains the error messages (copy content of slurm error log)
  * Otherwise: `done.log` is created (copy content of slurm stdout log)

The `slurm` directory contains supplementary informations about the slurm job processes.

#### Missing inputs list

The `$exp_name/$SAMPLE_DIRNAME/missing_inputs.tsv` file contains the missing inputs for each sample:

```html
arg_name    input_topic    input_tool    input_experiment    reason    help
GENOME      ASSEMBLY       UNICYCLER     default             not_run   "pbfbench asm unicycler run --help"
```

The reason is one of the following:

* `not_run` if the input experiment was not run or did not produce logs
* `missing_inputs` if at least one of the inputs of the input is missing
* `error` if the input experiment returned an error

The help column provides a potential solution.

#### Slurm logs

The `slurm` directory under `$exp_name/$SAMPLE_DIRNAME` contains the slurm logs for that samples:

* `command_steps_status.yaml` Status of each command step (initialization of the environment, command execution, and finalization of the environment)

  ```yaml
  init_env: $COMMAND_STATUS
  command: $COMMAND_STATUS
  close_env: $COMMAND_STATUS
  ```

  where `$COMMAND_STATUS` is one of the following:

  * `OK` if the step succeeded
  * `ERROR` if the step failed
  * `NULL` if the step did not return any state (yet)

  If one of the step status is `None`, the `sbatch` job state file `job_state.{SACCT_STATE}` can explain the reason why the step does not return any status (e.g. because of Slurm time limit reached).

* `job_state.{SACCT_STATE}` Job state given by the `sacct` command, if `sacct` returned something. See possible states in <https://slurm.schedmd.com/sacct.html#SECTION_JOB-STATE-CODES>
* `stats.psv` File containing the slurm run stats (Pipe Separated Value format, can be empty depending of `sacct` output)
* `stdout.log` Slurm stdout for that sample
* `stderr.log` Slurm stderr for that sample

### Internal process

The documentation [core/sbatch_run_process.md](core/sbatch_run_process.md) describes the internal process of the `sbatch` run process, and how `pbfbench` manages a job when it finishes
