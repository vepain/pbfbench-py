# Required in env_wrapper.sh:
#
# * export CLASSIFY_PY="path/to/plASgraph2/src/plASgraph2_classify.py"
# * export MODEL_DIR="path/to/plASgraph2/model/directory"

python3 ${CLASSIFY_PY} gfa ${GFA} ${MODEL_DIR} ${OUTFILE}
