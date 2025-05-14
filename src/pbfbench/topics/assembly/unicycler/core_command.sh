SHORT_READS_COLUMN_NUMBER=$(awk -v RS='\t' '/^short_reads/{print NR; exit}' ${SAMPLES_TSV})
SRR_ID=$(sed -n ${SLURM_ARRAY_TASK_ID}p ${SAMPLES_TSV} | cut -f${SHORT_READS_COLUMN_NUMBER})

READS_DIR=${WORK_EXP_SAMPLE_DIR}/reads
mkdir $READS_DIR

prefetch ${SRR_ID} --output-directory ${READS_DIR}
fastq-dump --split-3 --outdir ${READS_DIR} ${READS_DIR}/${SRR_ID}

FASTQ_1=${READS_DIR}/${SRR_ID}_1.fastq
FASTQ_2=${READS_DIR}/${SRR_ID}_1.fastq

gzip $FASTQ_1
FASTQ_1_GZ=${FASTQ_1}.gz
gzip $FASTQ_2
FASTQ_2_GZ=${FASTQ_2}.gz

unicycler -1 ${FASTQ_1_GZ} -2 ${FASTQ_2_GZ} -o ${WORK_EXP_SAMPLE_DIR} ${USER_TOOL_OPTIONS[@]}

gzip ${WORK_SAMPLE_EXP_DIR}/assembly.fasta
gzip ${WORK_SAMPLE_EXP_DIR}/assembly.gfa

rm -rf ${READS_DIR}
