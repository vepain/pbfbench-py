# Change log

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> 'M', 'm' and 'p' are respectively corresponding to major, minor and patch

<!-- The order of keywords:
## [Unreleased] - yyyy-mm-dd

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security
-->

<!-- next-header -->
## [Unreleased] - yyyy-mm-dd

### Added

* When `init` subcommand exists, add it to `run` subcommand process (with option to not initialize the experiment)

### Changed

* Tree file structure in data directory
* Big internal refactoring

### Fixed

* Manage `sbatch` externality

## [0.4.0] - 2025-05-14

### Added

* Add `BINNING` Topic with a new tool: `PANGEBIN_ONCE`
* New `ASSEMBLY` tool: `UNICYCLER`
* `GFA_CONNECTOR` tool implements FASTA assembly result
* Command script declare samples TSV path
* Each experiment is associated with a date, writen in a file `EXP_DIR/date.txt`

### Changed

* Precise all the builders, status classes, functions for tools with only options and those with arguments
* Precise `DataManager` and `WorkManager` classes for experiment file system managers
* Refactor `run` app functions to extract common parts with `init` app functions
* Move `origin_command` tool Result method to `missing_inputs` module (simplify convertion)

## [0.3.0] - 2025-05-11

### Added

* `PLASMIDNESS` topic
* `PLASMIDNESS/PLASCLASS` tool
* `PLASMIDNESS/PLASGRAPH2` tool (for plASgraph2)

### Changed

* Make `work_exp_fs_manager` an object attribute of `abc_tool_res_items.Result`
* `ASSEMBLY` topic command changes from `asm` to `assembly`

### Fixed

* `is_a_command` function now checks an end backslash (the command is not terminated)
* Assembly GFA result visitor
* Experiment `ErrorsTSVWriter` for append mode (`a`) now reads existing header

## [0.2.0] - 2025-05-09

### Changed

* Simplify Bash lines builder, generalize the Commands class
* `src/pbfbench/topics/TOPIC/TOOL/core_command.sh` make the core command bash script clearer
* Add a sbatch status system that communicates with the sample status

### Fix

* Sbatch script can exit before setting the sample directory, use another status system

## [0.1.1] - 2025-05-05

### Fixed

* `config` app now gives only tools providing topic results

## [0.1.0] - 2025-05-05

### Added

* `config` subcommand to obtain experiment draft configuration
* Log prints

### Changed

* Exp sample dir name separator from `_` to `-` to be coherent with already existing experiments
* Decompose the sbatch script and call the command part with `srun`

### Fixed

* Script line writting process
* Check read/write permissions of data and working directories

## [0.0.5] - 2025-05-01

### Fixed

* Assembly result classes were not original final class `Result`

## [0.0.4] - 2025-05-01

### Fixed

* Connector argument

## [0.0.3] - 2025-05-01

### Fixed

* Slurm config class `to_yaml_dump` method

## [0.0.2] - 2025-05-01

### Fixed

* Wrong config type in `Connector`

## [0.0.1] - 2025-05-01

### Added

* `run` command now verifies the tool environment script existence

### Changed

* Simplify API

## [0.0.0] - 2025-05-01

Init release.
