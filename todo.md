# To-dos

## Refactoring

* [ ] Uniformize: `run` exp config checks (and `config` subcmd) are not the same as in `init` exp config checks (difference of tool coverage in visitors)

## Logs

* [ ] Add sbatch error status to sample error reasons (except error close env which can be a sample warning status file)
  * [ ] Add list of sample warnings in exp warning tsv file

## Features

### User interface

* [ ] Add `--all` option for `init` subcommand
* [ ] Add a command `complete` to finish managing sbatch jobs (in case pbfbench cmd run falled in a time limit)

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
