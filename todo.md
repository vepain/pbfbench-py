# To-dos

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
