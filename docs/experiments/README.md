# Experiments

Example for downloading Illumina reads of the samples:

```yaml
name: NCBI_raw
arguments:  # SRA arguments,
# empty for Illumina paired-end read download (sample_id is auto filled)
options:  # SRA options
  ...
```

## Experiment outputs

Each sample is associated to a directory names `SAMPLE_DIRNAME=${species_id}_${sample_id}` in the experiment directory:

```sh
DATA_DIR/WORK_DIR
├── $TOPIC_NAME  # e.g. ASSEMBLY
│   └── $TOOL_NAME  # e.g. UNICYCLER
│       ├── $exp_name  # e.g. default
│       │   ├── $SAMPLE_DIRNAME  # e.g. ecol_SAMN10432165
│       │   │   ├── ...  # e.g. Unicycler output files
│       │   │   └── done.log | errors.log | missing_inputs.tsv  # to mark the status of the sample experiment
│       │   ├── ...  # Other samples
│       │   ├── scripts  # Slurm run scripts
│       │   │   └── YYYY-MM-DD_HH-MM-SS_run.sh  # Slurm run script according to the horodatage
│       │   ├── logs  # slurm logs
│       │   │   ├── errors.tsv  # Lists of samples with error (missing inputs or error during slurm run)
│       │   │   ├── slurm_%A_%a.out  # stdout for each sample
│       │   │   └── slurm_%A_%a.err  # stderr for each sample
│       │   └── exp_config.yaml  # Configurations of the experiment on the tool for the topic
│       └── env_wrapper.sh  # Tool environment wrapper script (In DATA_DIR tree, mirrored in WORK_DIR tree)
└── samples.tsv  # Only in DATA_DIR
```

The benchmark manager `pbfbench` communicates the end of an experiment in each sample directory `$SAMPLE_DIRNAME` with a system of files:

* If at least one input is missing (see later for missing reasons):
  * `missing_inputs.tsv` lists the missing inputs and their reasons
* Otherwise:
  * If one thing fails during the slurm script execution: `errors.log` contains the error messages (copy content of slurm error log)
  * Otherwise: `done.log` is created (copy content of slurm stdout log)

Note that the slurm log are always available in `$exp_name/logs` directory

### Sample missing inputs

The `$exp_name/$SAMPLE_DIRNAME/missing_inputs.tsv` file contains the missing inputs for each sample:

```html
arg_name    input_topic    input_tool    input_experiment    reason    help
GENOME      ASSEMBLY       UNICYCLER     default             not_run   "pbfbench asm unicycler run --help"
```

The reason is one of the following:

* `not_run` if the input experiment was not run or did not produce logs
* `missing_inputs` if at least one of the inputs of the input is missing
* `error` if the input experiment returned an error

The help column provide potential solution.

### Experiment errors list

<!-- TODO generalize OR NOT format and do it -->

The `$exp_name/logs/errors.tsv` file contains the list of samples with missing inputs or error during the slurm execution:

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
