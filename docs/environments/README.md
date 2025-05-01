# Example of using the environment wrapper


## Environment config

Each tool is associated with a environment context script. For a topic `$TOPIC` and a tool `$TOOL`, the environment context script file is: `DATA_DIR/$TOPIC/$TOOL/env_wrapper.sh`.

The example file is in `docs/environments`

## Script to describe the environment context

It is constitutes in two parts:

* The init part
* The close part

Each part is separated by magic comments.
The magic comments are:

* `# PBFBENCH BEGIN_ENV`
* `# PBFBENCH MID_ENV`
* `# PBFBENCH END_ENV`

`docs/environments/env_wrapper.sh` is an example of such script:

```sh
# text before begin

# PBFBENCH BEGIN_ENV ====

source ./virtualenv_tool/bin/activate
load cluster_binary/0.1.2

# PBFBENCH MID_ENV ----

deactivate
unload cluster_binary/0.1.2

# PBFBENCH END_ENV ====

# text after end

```

## Tests on the environment wrapper

### Iterate over the script lines that init the environment

```sh
# PBFBENCH BEGIN_ENV ====

source ./virtualenv_tool/bin/activate
load cluster_binary/0.1.2

# PBFBENCH MID_ENV ----
```

### Iterate over the script lines that close the environment

```sh
# PBFBENCH MID_ENV ----

deactivate
unload cluster_binary/0.1.2

# PBFBENCH END_ENV ====
```
