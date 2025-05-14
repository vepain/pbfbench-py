"""PlasBin-flow plasmidness input operations logics."""

import gzip
from pathlib import Path

import pbfbench.topics.assembly.visitor as asm_visitor


def parse_gfa(gfa_gz: Path, assembler: asm_visitor.Tools) -> dict:
    """Parse GFA file and return contigs dictionary."""
    contigs_dict = {}
    with gzip.open(gfa_gz, "r") as f:
        for line in f:
            gfa_line_array = line.decode()
            if gfa_line_array[0] == "S":
                match assembler:
                    case asm_visitor.Tools.GFA_CONNECTOR:
                        details = gfa_line_array[:-1].split("\t")
                        contig_id = details[1]
                        contig_name = (
                            details[0] + details[1] + "_" + "_".join(details[3:])
                        )
                        # FIXME [ANIKET] why?
                        # Because contig name in FASTA and GFA differ
                        # GFA contig names have ':' in them to figure out a GFA segment
                        # is a subsequence of a FASTA contig
                        # FIXME [ANIKET] why renamed contig name for SKESA (_ instead of :)
                    case asm_visitor.Tools.UNICYCLER:
                        details = gfa_line_array.split("\t")
                        contig_id = details[1]
                        contig_name = str(contig_id)
                    case _:
                        _err_msg = f"Unknown assembler {assembler}"
                        raise ValueError(_err_msg)

                contigs_dict[contig_id] = {
                    "Prob_Chromosome": 0.5,
                    "Prob_Plasmid": 0.5,
                    "Prediction": "Chromosome",
                    "Contig_name": contig_name,
                    "Contig_length": len(details[2]),
                }
    return contigs_dict
