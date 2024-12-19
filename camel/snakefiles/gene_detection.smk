from pathlib import Path

from camel.app.utils.genedetection.genedetectionutils import GeneDetectionUtils
from camel.app.utils.snakemake.snakemakeutils import SnakemakeUtils
from camel.app.utils.step.step import Step
from camel.snakefiles import gene_detection


# Include workflows for the different detection methods
include: gene_detection.SNAKEFILE_GENE_DETECTION_BLAST

# Common rules
rule gene_detection_db_manager:
    """
    Retrieves the FASTA file and the metadata from a database folder.
    """
    output:
        FASTA = Path(config['working_dir']) / 'gene_detection' / '{db}' / 'db_manager' / 'fasta.io',
        FASTA_clustered = Path(config['working_dir']) / 'gene_detection' / '{db}' / 'db_manager' / 'fasta-clust.io',
        INFORMS = Path(config['working_dir']) / 'gene_detection' / '{db}' / 'db_manager' / 'informs.io'
    params:
        db_path = lambda wildcards: config['gene_detection'][wildcards.db]['path'],
        running_dir = lambda wildcards: Path(config['working_dir']) / 'gene_detection' / wildcards.db
    run:
        from camel.app.io.tooliodirectory import ToolIODirectory
        from camel.app.tools.genedetection.dbmanager import DBManager
        db_manager = DBManager()
        db_manager.add_input_files({'DIR': [ToolIODirectory(Path(str(params.db_path)))]})
        step = Step(str(rule), db_manager, Path(str(params.running_dir)))
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(db_manager, output)

rule gene_detection_get_hits:
    """
    Retrieves the hits based on the detection method species in the configuration.
    """
    input:
        INFORMS_DB = rules.gene_detection_db_manager.output.INFORMS,
        VAL_hits = lambda wildcards: str(Path(config['working_dir']) / str(gene_detection.OUTPUT_GENE_DETECTION_HITS_METHOD).format(
            db=wildcards.db, method=GeneDetectionUtils.get_detection_method_key(config, wildcards.db))),
        INFORMS_hits = lambda wildcards: str(Path(config['working_dir']) / str(gene_detection.OUTPUT_GENE_DETECTION_INFORMS_METHOD).format(
            db=wildcards.db, method=GeneDetectionUtils.get_detection_method_key(config, wildcards.db)))
    output:
        VAL_hits = Path(config['working_dir']) / 'gene_detection' / '{db}' / 'hit_selection' / 'hits-standardized.io',
        INFORMS = Path(config['working_dir']) / gene_detection.OUTPUT_GENE_DETECTION_INFORMS
    run:
        import shutil
        shutil.copyfile(str(input.VAL_hits), output.VAL_hits)
        # Add a tag for the database to distinguish commands in the output
        informs = SnakemakeUtils.load_object(Path(str(input.INFORMS_hits)))
        informs['_tag'] = SnakemakeUtils.load_object(Path(str(input.INFORMS_DB)))['title']
        SnakemakeUtils.dump_object(informs, Path(output.INFORMS))

rule gene_detection_map_names:
    """
    Maps the standardized names (seq_X) to the original ones.
    Renames the TSV file based on the sample name and database.
    """
    input:
        INFORMS_db = rules.gene_detection_db_manager.output.INFORMS,
        HITS = rules.gene_detection_get_hits.output.VAL_hits
    output:
        HITS = Path(config['working_dir']) / gene_detection.OUTPUT_GENE_DETECTION_ALL_HITS,
        TSV = Path(config['working_dir']) / 'gene_detection' / '{db}' / 'metadata' / 'tsv.io'
    params:
        dir_working = lambda wildcards: Path(config['working_dir']) / 'gene_detection' / wildcards.db / 'metadata',
        sample_name = config['sample_name'],
        db_config = lambda wildcards: config['gene_detection'][wildcards.db]
    run:
        from camel.app.io.tooliofile import ToolIOFile
        from camel.app.io.tooliovalue import ToolIOValue
        from camel.app.utils.fileutils import FileUtils
        informs_db = SnakemakeUtils.load_object(Path(input.INFORMS_db))
        hits = SnakemakeUtils.load_object(Path(input.HITS))

        # Map standardized names to original ones
        hits_updated = []
        for hit in [io.value for io in hits]:
            seq_id = hit.locus
            hit.locus = informs_db['mapping'].get_metadata(seq_id, 'allele')
            hit.accession = informs_db['mapping'].get_metadata(seq_id, 'accession', '-')
            if params.db_config.get('metadata') is not None:
                key = params.db_config['metadata']['key']
                hit.add_metadata(params.db_config['metadata']['name'], informs_db['mapping'].get_metadata(seq_id, key))
            hits_updated.append(hit)
        SnakemakeUtils.dump_object([ToolIOValue(hit) for hit in hits_updated], Path(output.HITS))

        # Save tabular output
        if len(hits_updated) >= 1:
            output_path = Path(str(params.dir_working)) / 'hits-{}-{}.tsv'.format(
                FileUtils.make_valid(params.sample_name), FileUtils.make_valid(informs_db['name']))
            with output_path.open('w') as handle:
                handle.write('\t'.join(hits_updated[0].table_column_names))
                handle.write('\n')
                for hit in hits_updated:
                    handle.write('\t'.join(hit.to_table_row()))
                    handle.write('\n')
            SnakemakeUtils.dump_object([ToolIOFile(output_path)], Path(output.TSV))
        else:
            SnakemakeUtils.dump_object([], Path(output.TSV))

rule gene_detection_report:
    """
    Creates HTML reports for the gene detection.
    """
    input:
        VAL_Hits = rules.gene_detection_map_names.output.HITS,
        TSV = rules.gene_detection_map_names.output.TSV,
        INFORMS_db_info = rules.gene_detection_db_manager.output.INFORMS,
        INFORMS_detection = rules.gene_detection_get_hits.output.INFORMS
    output:
        VAL_HTML = Path(config['working_dir']) / gene_detection.OUTPUT_GENE_DETECTION_REPORT
    params:
        running_dir = lambda wildcards: Path(config['working_dir']) / 'gene_detection' / wildcards.db / 'report',
        config_data = lambda wildcards: config['gene_detection'][wildcards.db]
    run:
        from camel.app.tools.genedetection.htmlreportergenedetection import HtmlReporterGeneDetection
        reporter = HtmlReporterGeneDetection()
        step = Step(str(rule), reporter, Path(str(params.running_dir)))
        if 'force_detection_method' in params.config_data:
            reporter.update_parameters(forced_detection_method = params.config_data['force_detection_method'])
        SnakemakeUtils.add_pickle_inputs(reporter, input)
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(reporter, output)

rule gene_detection_create_empty_report:
    """
    Creates an empty HTML report for the gene detection.
    """
    input:
        INFORMS_db_info = rules.gene_detection_db_manager.output.INFORMS
    output:
        VAL_HTML = Path(config['working_dir']) / gene_detection.OUTPUT_GENE_DETECTION_REPORT_EMPTY
    params:
        running_dir = lambda wildcards: Path(config['working_dir']) / 'gene_detection' / wildcards.db / 'report'
    run:
        from camel.app.utils.report.htmlreportsection import HtmlReportSection
        from camel.app.io.tooliovalue import ToolIOValue
        db_info = SnakemakeUtils.load_object(Path(input.INFORMS_db_info))
        section = HtmlReportSection(db_info['title'], 3)
        section.add_paragraph('Analysis disabled')
        SnakemakeUtils.dump_object([ToolIOValue(section)], Path(output.VAL_HTML))

rule gene_detection_dump_summary_info:
    """
    Dumps the summary information from the gene detection in tabular format.
    """
    input:
        INFORMS_hits = Path(config['working_dir']) / 'gene_detection' / '{db}' / 'hit_selection' / 'selected-hits.io'
    output:
        TSV = Path(config['working_dir']) / gene_detection.OUTPUT_GENE_DETECTION_SUMMARY
    run:
        import json
        informs = SnakemakeUtils.load_object(Path(input.INFORMS_hits))
        hit_info = []
        blast_stats = []
        for hit in informs:
            hit_info.append(hit.value.to_table_row())
        with open(output.TSV, 'w') as handle:
            handle.write('hits_{}\t{}'.format(wildcards.db, json.dumps(hit_info)))
            handle.write('\n')
