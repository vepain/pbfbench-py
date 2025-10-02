# Required in env_wrapper.sh:
#
# * export CLASSIFY_FASTA_PY="path/to/plasclass/src/classify_fasta.py"

python3 "${CLASSIFY_FASTA_PY}" --fasta "${FASTA}" --outfile "${OUTFILE}" "${USER_TOOL_OPTIONS[@]}"
