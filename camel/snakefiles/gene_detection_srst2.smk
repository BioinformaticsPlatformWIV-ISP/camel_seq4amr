from pathlib import Path

from camel.app.utils.fastqutils import FastqUtils
from camel.app.utils.snakemake.snakemakeutils import SnakemakeUtils
from camel.app.utils.step.step import Step
from camel.snakefiles import gene_detection


rule gene_detection_srst2:
    """
    Read-mapping based gene detection using SRST2.
    Input is a pickled dictionary with ToolIO files with either 'FASTQ_PE' or 'FASTQ_SE' as key.
    If paired end input is provided, the read status ('_1', '_1P') is determined based on the read name. 
    """
    input:
        IO = Path(config['working_dir']) / 'fq_dict.io',
        FASTA = Path(config['working_dir']) / 'gene_detection' / '{db}' / 'db_manager' / 'fasta-clust.io'
    output:
        TSV = Path(config['working_dir']) / 'gene_detection' / '{db}' / 'srst2' / 'tsv-srst2.io',
        INFORMS = Path(config['working_dir']) / str(gene_detection.OUTPUT_GENE_DETECTION_INFORMS_METHOD).format(db='{db}', method='srst2')
    params:
        running_dir = lambda wildcards: Path(config['working_dir']) / 'gene_detection' / wildcards.db / 'srst2',
        db_config = lambda wildcards: config['gene_detection'][wildcards.db],
        max_divergence = lambda wildcards: config['gene_detection'][wildcards.db].get('params', {}).get('srst2', {}).get('max_divergence', 10),
        min_coverage = lambda wildcards: config['gene_detection'][wildcards.db].get('params', {}).get('srst2', {}).get('min_coverage', 60),
        max_unaligned_overlap = lambda wildcards: config['gene_detection'][wildcards.db].get('params', {}).get('srst2', {}).get('max_unaligned_overlap', 10),
        max_mismatch = lambda wildcards: config['gene_detection'][wildcards.db].get('params', {}).get('srst2', {}).get('max_mismatch', 10),
        read_type = 'SE' if config.get('read_type') == 'iontorrent' else 'PE'
    threads: 4
    run:
        from camel.app.utils.snakemake.snakepipelineutils import SnakePipelineUtils
        from camel.app.tools.srst2.srst2gene import Srst2Gene
        dir_working = Path(str(params.running_dir))
        if not dir_working.exists():
            dir_working.mkdir(parents=True)
        srst2 = Srst2Gene()
        SnakemakeUtils.add_pickle_input(srst2, 'FASTA', Path(input.FASTA))
        fq_input_dict = SnakePipelineUtils.extracts_fq_input(
            Path(input.IO), key_pe='FASTQ_PE', key_se='FASTQ_SE', read_type=params.read_type)
        srst2.add_input_files(fq_input_dict)
        step = Step(str(rule), srst2, Path(str(params.running_dir)), wildcards)

        # Update parameters
        srst2.update_parameters(threads=threads)
        if 'FASTQ_PE' in fq_input_dict:
            fwd_read_path = fq_input_dict['FASTQ_PE'][0].path
            fwd_designator, rev_designator = FastqUtils.determine_read_status(fwd_read_path)
            srst2.update_parameters(forward_designator=fwd_designator, reverse_designator=rev_designator)
        srst2.update_parameters(
            max_divergence=str(params.max_divergence),
            min_coverage=str(params.min_coverage),
            max_unaligned_overlap=str(params.max_unaligned_overlap),
            max_mismatch=str(params.max_mismatch)
        )

        # Run tool
        step.run_step()
        SnakemakeUtils.dump_object(srst2.informs, Path(output.INFORMS))
        if 'TSV' in srst2.tool_outputs:
            SnakemakeUtils.dump_tool_output(srst2, 'TSV', Path(output.TSV))
        else:
            SnakemakeUtils.dump_object([], Path(output.TSV))

rule gene_detection_srst2_hit_extraction:
    """
    Extracts hits from the SRST2 output.
    """
    input:
        TSV = rules.gene_detection_srst2.output.TSV
    output:
        VAL_Hits = Path(config['working_dir']) / str(gene_detection.OUTPUT_GENE_DETECTION_HITS_METHOD).format(db='{db}', method='srst2')
    params:
        running_dir = lambda wildcards: Path(config['working_dir']) / 'gene_detection' / wildcards.db / 'srst2',
    run:
        from camel.app.tools.genedetection.srst2hitextractor import SRST2HitExtractor
        extractor = SRST2HitExtractor()
        step = Step(str(rule), extractor, Path(str(params.running_dir)), wildcards)
        SnakemakeUtils.add_pickle_inputs(extractor, input)
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(extractor, output)
