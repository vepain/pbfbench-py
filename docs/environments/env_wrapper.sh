# text before begin

# PBFBENCH BEGIN_ENV ====

source ./virtualenv_tool/bin/activate
load cluster_binary/0.1.2

# PBFBENCH MID_ENV ----

deactivate
unload cluster_binary/0.1.2

# PBFBENCH END_ENV ====

# text after end
