from pathlib import Path


SNAKEFILE_ASSEMBLY_SPADES = f'{Path(__file__).parent / Path(__file__).stem}.smk'

_dir_spades = Path('assembly_spades')
OUTPUT_ASSEMBLY_FASTA = _dir_spades / 'filtering' / 'fasta.io' 
OUTPUT_ASSEMBLY_INFORMS = _dir_spades / 'spades' / 'informs.io' 
OUTPUT_ASSEMBLY_FILTERING_INFORMS = _dir_spades / 'filtering' / 'informs.io' 
OUTPUT_ASSEMBLY_REPORT = _dir_spades / 'report' / 'html.io' 
OUTPUT_ASSEMBLY_SUMMARY = _dir_spades / 'summary' / 'summary_out.tsv' 
OUTPUT_ASSEMBLY_MAPPING_INFORMS = _dir_spades / 'bowtie2' / 'informs.io' 
OUTPUT_ASSEMBLY_DEPTH_INFORMS = _dir_spades / 'samtools_depth' / 'informs.io' 
