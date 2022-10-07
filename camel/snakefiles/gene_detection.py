from pathlib import Path
from typing import Any, Dict, Optional

SNAKEFILE_GENE_DETECTION = f'{Path(__file__).parent / Path(__file__).stem}.smk'
SNAKEFILE_GENE_DETECTION_BLAST = f'{Path(__file__).parent / Path(__file__).stem}_blast.smk'
SNAKEFILE_GENE_DETECTION_KMA = f'{Path(__file__).parent / Path(__file__).stem}_kma.smk'
SNAKEFILE_GENE_DETECTION_SRST2 = f'{Path(__file__).parent / Path(__file__).stem}_srst2.smk'
_dir_gene_detection = Path('gene_detection') / '{db}'

# Input files and database
GENE_DETECTION_FASTA = _dir_gene_detection / 'db_manager' / 'fasta.io'
GENE_DETECTION_FASTA_CLUSTERED = _dir_gene_detection / 'db_manager' / 'fasta-clust.io'
INPUT_GENE_DETECTION_FASTA = _dir_gene_detection / 'input' / 'fasta.io'

# Generic output paths with a wildcard for the detection method
OUTPUT_GENE_DETECTION_HITS_METHOD = _dir_gene_detection / '{method}' / 'hits.io'
OUTPUT_GENE_DETECTION_INFORMS_METHOD = _dir_gene_detection / '{method}' / 'informs.io'

# Selected hits and informs for the given database
OUTPUT_GENE_DETECTION_ALL_HITS = _dir_gene_detection / 'hit_selection' / 'selected-hits.io'
OUTPUT_GENE_DETECTION_INFORMS = _dir_gene_detection / 'hit_selection' / 'informs.io'
OUTPUT_GENE_DETECTION_COLUMNS = _dir_gene_detection / 'report' / 'informs-columns.io'

OUTPUT_GENE_DETECTION_TSV_BLAST = _dir_gene_detection / 'hit_filtering' / 'tsv-filtered.io'
OUTPUT_GENE_DETECTION_TSV_SRST2 = _dir_gene_detection / 'hit_extraction' / 'tsv-srst2.io'

# Report and summary outputs
OUTPUT_GENE_DETECTION_REPORT = _dir_gene_detection / 'report' / 'html.io'
OUTPUT_GENE_DETECTION_REPORT_EMPTY = _dir_gene_detection / 'report' / 'html-empty.io'
OUTPUT_GENE_DETECTION_SUMMARY = _dir_gene_detection / 'report' / 'summary_out.tsv'


def get_gene_detection_report(db_key: str, config: Dict[str, Any], analysis_name: Optional[str] = None) -> str:
    """
    Returns the report input for the given database key.
    :param db_key: Database key
    :param config: Pipeline config
    :param analysis_name: Analysis name that is checked
    :return: Report input path
    """
    search_key = analysis_name if analysis_name is not None else db_key
    if search_key not in config['analyses']:
        return Path(config['working_dir']) / str(OUTPUT_GENE_DETECTION_REPORT_EMPTY).format(db=db_key)
    return Path(config['working_dir']) / str(OUTPUT_GENE_DETECTION_REPORT).format(db=db_key)
