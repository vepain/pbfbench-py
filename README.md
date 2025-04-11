# PlasBin-flow benchmarking framework

## Setup Python virtual environment

### With conda

<!-- DOCU condaenv for dev -> change when user's one is ready -->
* [*For dev*] Create the conda environment

  ```sh
  conda env create -n pbfbench-dev -f config/condaenv_313-dev.yml
  ```

* [*For dev*] Activate the conda environment

  ```sh
  conda activate pbfbench-dev
  ```

### With virtualenv

```sh
python3.13 -m virtualenv .venv_pbfbench_313
source ./.venv_pbfbench_313/bin/activate  # active.fish for fish shell...
pip install .  # `pip install -e .` for editable mode i.e. for dev
```

## Usage

```sh
pbfbench --help
```

## Create automatic documentation

```sh
pbfbench doc auto  # creates autodoc in `docs` directory
pbfbench doc clean  # to clean the auto documentation
```
