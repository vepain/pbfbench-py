# PlasBin-flow benchmarking framework

## Benchmark file tree structure

The data directory contains cold data (`DATA_DIR`), while the working directory (`WORK_DIR`) acts as a temporary storage for the outputs of running tools.
At the end of the runs, the files are moved to the `DATA_DIR` directory, respecting the same structure.

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

The `exp_config.yaml` file contains the configuration for the experiment.
The structure is defined bellow, and the examples are for a binning tool:

```yaml
name: $exp_name  # e.g. MinLen1000
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
```

## Python program to launch experiments

A typical call to the command is:
<!-- DOCU fix command args order -->
```sh
pbfbench $topic_cmd $tool_cmd run $data_dir $work_dir $slurm_cfg_yaml $exp_cfg_yaml [--rerun]
```

where:

* `topic_cmd` is the command associated to the topic (e.g. `asm` for assembly)
* `tool_cmd` is the command associated to the tool (e.g. `unicycler` for Unicycler)
* `data_dir` is the path to the data directory
* `work_dir` is the path to the working directory
* `slurm_cfg_yaml` is the path to the SLURM configuration file
* `exp_cfg_yaml` is the path to the experiment configuration file

The `tools_env_cfg_yaml` file give for each tool how to init and to close their running environment:

The `slurm_cfg_yaml` provides the SLURM configuration:

```yaml
- "--mem=36"
- "--cpus-per-task=16"
...  # except options for array jobs, which are automatically set
```

See more details about the experiments in [environments/README.md](environments/README.md)