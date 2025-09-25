# To-dos

## Tasks stack

*From top to bottom:*

* [x] Move experiment name from the configuration to the command lines
  * [x] Update the doc
  * [x] Be carefull of comparing properly two tool configurations
* [x] Separate experiment config from SLURM configuration
  * [x] Change the doc
  * [x] Be carefull of comparing properly two tool configurations
* [x] Refactoring tool config to tool connector (merge of config and connector)
* [ ] Fix run/format/resume stages
* [ ] Verify data dire and work dir are not the same!
  * [ ] Update doc

## Refactoring

* [ ] Uniformize: `run` exp config checks (and `config` subcmd) are not the same as in `init` exp config checks (difference of tool coverage in visitors)
* [ ] Bad pattern design: connector links experiment `ConfigWithArguments` with tool `Results` visitor, while the validity of the config depends on the visitor. The config should be directly linked to the visitor and check its validity during its construction.

## Logs

* [ ] Add sbatch error status to sample error reasons (except error close env which can be a sample warning status file)
  * [ ] Add list of sample warnings in exp warning tsv file

## Features

### User interface

* [ ] Add `--all` option for `init` subcommand

### Assembly Topic

* [ ] SKESA
* [ ] Unicycler
* [ ] GFA connector
  * [ ] Format the GFA contig name and add segment property "SC" a str equals to the previous name
  * [ ] Export FASTA from modified GFA
* [ ] Check if GFA must be standardized (which type of standardization?)

### SEEDS Topic

* [ ] Platon results logics

### PLASMIDNESS Topic

Both run and result logics

* [x] PlasClass
  * [x] Output file: `plasmid_probabilities.tsv`
* [ ] PlasGraph2
* [ ] RFPlasmid
* [ ] MLPlasmids (R managment and species name)

  >[!WARNING]
  > It seems some tools (MLPlasmids) need the full name of the species, which thus must be specified in the `samples.tsv` file.
  > Or instead Python should set the variable according the column header used (enables type verification).
  > MLPlasmids is not the priority for this project.

### BINNING Topic

* [ ] Format seeds results
  * [ ] c.f. all seeds tools
* [ ] Format plasmidness results
  * [ ] c.f. all plasmidness tools

### Helpers

Help for Cedar `env_wrapper.sh` files in `tmp_vepain/features/env_wrappers_helps`

Help for running scripts lines builders in `tmp_vepain/features/run_scripts`

## In progress

* [ ] Get stats of last running experiment
  * [ ] In progress or not
  * [ ] Number of success / error details etc.
* [ ] Get DAG of experiments with summary on success and errors (mermaid diagramm)

### Core

#### Monitoring status

* [ ] Check experiment has been launched
  * [ ] check `date.txt` or `config.yaml` files exist
    * [ ] #FIXME be sure to write these files at the really beggining of the exp launch
* [ ] Check experiment is running
  * [ ] Use `sacct`
* [ ] Check experiment is finished
  * [ ] No `sacct` or `sacct` returned finish state
* [ ] Check success of samples (in the `data` directory)
  * With `done.txt`

#### Already running experiment

* [ ] Check if the experiment is not already running but with a different working directory
  * [ ] transform `date.txt` -> `last_run.yaml` which would contain the date and the working directory

### User-friendly

* [ ] Command `pbfbench topic-cmd tool-cmd run $EXP_NAME $DATA_DIR $WORK_DIR $CONFIG_YAML [--not-run] [--missing-inputs] [--error] [--success] [--all]` (by default, `--not-run`)
  * Cumulative options `--not-run` `--missing-inputs` `--error` `--success`
  * Option `--all` rerun all the samples (does not consider the above cumulative options)
* [ ] Be sure `run` also `init` when required
* [ ] Command `pbfbench topic-cmd tool-cmd status $EXP_NAME $DATA_DIR [--report/-r=YAML]`
  * [ ] `In progress` or `Finished`
    * print done (success, errors), not done
  * [ ] `No experiment of name... for topic... and tool...`
  * [ ] API to read report YAML file
* [ ] Command `pbfbench topic-cmd tool-cmd resume $EXP_NAME $DATA_DIR`

## To Fix

* [x] #FIXME samples with missing inputs should not stay in the work dir
  * Use of `WORK_DIR/.../$exp_name/sample_status.tsv` file
* [x] #FIXME when resume a run, be sure to take into account the samples with missing inputs
  * Use of `WORK_DIR/.../$exp_name/sample_status.tsv` file
* [x] #FIXME if not in progress, and work/topic/tool/exp dir already exists, clean it.
* [x] #DOCU what happens if sacct do not return a state for a sample (e.g. during a run resume)?
  * Return error status
* [x] #FIXME Remove samples in data when they rerun
  * At the end of their resolve
