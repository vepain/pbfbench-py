# To-dos

* [ ] Run exp config checks (and config subcmd) are not the same as exp config checks for init subcmd (difference of tool coverage in visitors)
* [ ] PBF format seeds (`pbf_seeds.tsv`)
* [ ] PBF format plasmidness (`pbf_plasmidness.tsv`)

>[!WARNING]
> It seems some tools (MLPlasmids) need the full name of the species, which thus must be specified in the `samples.tsv` file
> MLPlasmids is not the priority for this project.

## Logs

* [ ] Add sbatch error status to sample error reasons (except error close env which can be a sample warning status file)
  * [ ] Add list of sample warnings in exp warning tsv file

## Limitations

* [ ] (To document) The environment wrapper logics are not robust for commands with inline comments (do not finish a command with a comment)

## Features

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

### BINNING Topic

* [ ] Format seeds results
  * [ ] c.f. all seeds tools
* [ ] Format plasmidness results
  * [ ] c.f. all plasmidness tools

### Helpers

Help for Cedar `env_wrapper.sh` files in `tmp_vepain/features/env_wrappers_helps`

Help for running scripts lines builders in `tmp_vepain/features/run_scripts`
