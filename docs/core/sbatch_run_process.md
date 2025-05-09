# How pbfbench manages sbatch jobs?

Pbfbench writes files only in the working directory until all the sbatch jobs finish.
Each sbatch job marks its end in the temporary `EXP_NAME/logs` directory.

```sh
WORK_DIR
└── $TOPIC_NAME  # e.g. ASSEMBLY
    └── $TOOL_NAME  # e.g. UNICYCLER
        └── $exp_name  # e.g. default
            ├── $SAMPLE_DIRNAME  # e.g. ecol-SAMN10432165
            │   └── ...  # e.g. Unicycler output files
            ├── ...  # Other samples
            ├── logs  # Temporary logs directory, created before the sbatch run, deleted at the end of pbfbench run
            │   ├── array_job.id  # File containing the array job id (%A), deleted at the end of sbatch runs
            │   ├── slurm_%A_%a.out  # Slurm stdout for each sample
            │   ├── slurm_%A_%a.err  # Slurm stderr for each sample
            │   └── slurm_%A_%a.{init_env_error,command_error,close_env_error,end}  # Sbatch job status file
            ├── scripts  # Slurm run scripts
            │   ├── YYYY-MM-DD_HH-MM-SS_sbatch.sh  # Slurm run script according to the horodatage
            │   └── YYYY-MM-DD_HH-MM-SS_command.sh  # srun commands without init and close tool environment processes
            ├── errors.tsv  # Lists of samples with error (missing inputs or error during slurm run)
            └── config.yaml  # Configurations of the experiment on the tool for the topic
```

The sbatch status files in `logs` directory inform `pbfbench` the job finishes (with errors or not).
