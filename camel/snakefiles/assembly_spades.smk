from pathlib import Path

from camel.app.loggingutils import initialize_logging
from camel.app.utils.snakemake.snakemakeutils import SnakemakeUtils
from camel.app.utils.step.step import Step
from camel.snakefiles import assembly_spades

initialize_logging()


rule assembly_spades_run:
    """
    De-novo assembly using SPAdes.
    """
    input:
        IO = Path(config['working_dir']) / 'fq_dict.io'
    output:
        FASTA_Contig = Path(config['working_dir']) / 'assembly_spades' / 'spades' / 'fasta.io',
        INFORMS = Path(config['working_dir']) / assembly_spades.OUTPUT_ASSEMBLY_INFORMS
    params:
        running_dir = Path(config['working_dir']) / 'assembly_spades' / 'spades',
        spades_options = config.get('assembly', {}).get('spades', {}),
        read_type = 'SE' if config.get('read_type') == 'iontorrent' else 'PE'
    threads: 8
    priority: 1
    run:
        from camel.app.tools.spades.spades import SPAdes
        from camel.app.utils.snakemake.snakepipelineutils import SnakePipelineUtils
        spades = SPAdes()

        # Reformat FASTQ dictionary
        fq_dict = SnakePipelineUtils.extracts_fq_input(Path(input.IO), key_pe='FASTQ_PE_1', keys_se=[
            'FASTQ_SE_1', 'FASTQ_SE_2'], key_se='FASTQ_SE_1', drop_empty=True, read_type=params.read_type)
        spades.add_input_files(fq_dict)
        step = Step(str(rule), spades, Path(str(params.running_dir)), wildcards)
        spades.update_parameters(**params.spades_options)
        spades.update_parameters(threads=threads)
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(spades, output)

rule assembly_filter_contig_length:
    """
    Filters out the small contigs.
    """
    input:
        FASTA = rules.assembly_spades_run.output.FASTA_Contig
    output:
        FASTA = Path(config['working_dir']) / 'assembly_spades' / 'filtering' / 'fasta.io',
        INFORMS = Path(config['working_dir']) / assembly_spades.OUTPUT_ASSEMBLY_FILTERING_INFORMS
    params:
        running_dir = Path(config['working_dir']) / 'assembly_spades' / 'filtering',
        min_contig_length = config['assembly'].get('min_contig_length', 0) if 'assembly' in config else 0
    run:
        from camel.app.tools.seqtk.seqtkseq import SeqtkSeq
        seqtk = SeqtkSeq()
        SnakemakeUtils.add_pickle_inputs(seqtk, input)
        step = Step(str(rule), seqtk, Path(str(params.running_dir)), wildcards)
        seqtk.update_parameters(output_filename='assembly_filtered.fasta', min_length=params.min_contig_length)
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(seqtk, output)

rule assembly_quast:
    """
    Generates assembly statistics using QUAST.
    """
    input:
        FASTA = rules.assembly_filter_contig_length.output.FASTA
    output:
        TSV = Path(config['working_dir']) / 'assembly_spades' / 'quast' / 'tsv.io'
    params:
        running_dir = Path(config['working_dir']) / 'assembly_spades' / 'quast'
    run:
        from camel.app.tools.quast.quast import Quast
        quast = Quast()
        SnakemakeUtils.add_pickle_inputs(quast, input)
        step = Step(str(rule), quast, Path(str(params.running_dir)), wildcards)
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(quast, output)

rule assembly_quast_extract_informs:
    """
    Extracts the information from the QUAST output file.
    """
    input:
        TSV = rules.assembly_quast.output.TSV
    output:
        INFORMS = Path(config['working_dir']) / 'assembly_spades' / 'quast' / 'informs.io'
    params:
        running_dir = Path(config['working_dir']) / 'assembly_spades' / 'quast'
    run:
        from camel.app.tools.quast.quastinformextractor import QuastInformExtractor
        quast_inform_extractor = QuastInformExtractor()
        SnakemakeUtils.add_pickle_inputs(quast_inform_extractor, input)
        step = Step(str(rule), quast_inform_extractor, Path(str(params.running_dir)), wildcards)
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(quast_inform_extractor, output)

rule assembly_report:
    """
    Creates the HTML report for the assembly.
    """
    input:
        FASTA_Raw = rules.assembly_spades_run.output.FASTA_Contig,
        FASTA_Contig = rules.assembly_filter_contig_length.output.FASTA,
        INFORMS_spades = rules.assembly_spades_run.output.INFORMS,
        INFORMS_quast = rules.assembly_quast_extract_informs.output.INFORMS
    output:
        VAL_HTML = Path(config['working_dir']) / assembly_spades.OUTPUT_ASSEMBLY_REPORT
    params:
        running_dir = Path(config['working_dir']) / 'assembly_spades' / 'report',
        sample_name = config['sample_name']
    run:
        from camel.app.tools.reporters.reporterassembly import ReporterAssembly
        from camel.app.io.tooliovalue import ToolIOValue
        reporter = ReporterAssembly()
        reporter.add_input_files({
            'SAMPLE_NAME': [ToolIOValue(params.sample_name)], 'ASSEMBLER': [ToolIOValue('SPAdes')]})
        SnakemakeUtils.add_pickle_inputs(reporter, input)
        step = Step(str(rule), reporter, Path(str(params.running_dir)), wildcards)
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(reporter, output)

rule assembly_dump_summary_info:
    """
    Dumps the summary information from the assembly pipeline.
    """
    input:
        INFORMS_quast = rules.assembly_quast_extract_informs.output.INFORMS
    output:
        Path(config['working_dir']) / assembly_spades.OUTPUT_ASSEMBLY_SUMMARY
    params:
        running_dir = Path(config['working_dir']) / 'assembly_spades' / 'summary'
    run:
        quast_informs = SnakemakeUtils.load_object(Path(input.INFORMS_quast))
        summary_data = [
            ('assembly_n50', quast_informs['contig']['N50']),
            ('assembly_nb_contigs', quast_informs['contig']['# contigs']),
            ('assembly_total_length', quast_informs['genome']['Total length'])
        ]
        with open(output[0], 'w') as handle:
            for key, value in summary_data:
                handle.write(f'{key}\t{value}')
                handle.write('\n')

rule assembly_bt2_index:
    """
    Creates a bowtie2 index for the assembly.
    """
    input:
        FASTA_REF = rules.assembly_filter_contig_length.output.FASTA
    output:
        INDEX_GENOME_PREFIX = Path(config['working_dir']) / 'assembly_spades' / 'bowtie2' / 'genome_prefix.io'
    params:
        running_dir = Path(config['working_dir']) / 'assembly_spades' / 'bowtie2'
    run:
        from camel.app.tools.bowtie2.bowtie2index import Bowtie2Index
        bowtie2_index = Bowtie2Index()
        step = Step(str(rule), bowtie2_index, Path(str(params.running_dir)), wildcards)
        SnakemakeUtils.add_pickle_inputs(bowtie2_index, input)
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(bowtie2_index, output)

rule assembly_bt2_map:
    """
    Maps the reads against the assembled contigs.
    """
    input:
        IO = Path(config['working_dir']) / 'fq_dict.io',
        INDEX_GENOME_PREFIX = rules.assembly_bt2_index.output.INDEX_GENOME_PREFIX
    output:
        SAM = Path(config['working_dir']) / 'assembly_spades' / 'bowtie2' / 'sam.io',
        INFORMS = Path(config['working_dir']) / assembly_spades.OUTPUT_ASSEMBLY_MAPPING_INFORMS
    params:
        running_dir = Path(config['working_dir']) / 'assembly_spades' / 'bowtie2',
        read_type = 'SE' if config.get('read_type') == 'iontorrent' else 'PE'
    run:
        from camel.app.utils.snakemake.snakepipelineutils import SnakePipelineUtils
        from camel.app.tools.bowtie2.bowtie2map import Bowtie2Map
        bowtie2_map = Bowtie2Map()
        step = Step(str(rule), bowtie2_map, Path(str(params.running_dir)), wildcards)
        bowtie2_map.add_input_files(SnakePipelineUtils.extracts_fq_input(
            Path(input.IO), key_se='FASTQ_SE', drop_empty=True, read_type=params.read_type))
        SnakemakeUtils.add_pickle_input(bowtie2_map, 'INDEX_GENOME_PREFIX', Path(input.INDEX_GENOME_PREFIX))
        step.run_step()
        bowtie2_map.informs['_tag'] = 'Coverage calculation'
        SnakemakeUtils.dump_tool_outputs(bowtie2_map, output)

rule assembly_bt2_sam_to_bam:
    """
    Converts the SAM file generated by bowtie2 to BAM format.
    """
    input:
        SAM = rules.assembly_bt2_map.output.SAM
    output:
        BAM = Path(config['working_dir']) / 'assembly_spades' / 'bowtie2' / 'bam.io'
    params:
        running_dir = Path(config['working_dir']) / 'assembly_spades' / 'bowtie2'
    run:
        from camel.app.tools.samtools.samtoolsview import SamtoolsView
        samtools_view = SamtoolsView()
        step = Step(str(rule), samtools_view, Path(str(params.running_dir)), wildcards)
        SnakemakeUtils.add_pickle_inputs(samtools_view, input)
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(samtools_view, output)

rule assembly_bt2_sort_bam:
    """
    Sorts the BAM alignment.
    """
    input:
        BAM = rules.assembly_bt2_sam_to_bam.output.BAM
    output:
        BAM = Path(config['working_dir']) / 'assembly_spades' / 'bowtie2' / 'bam_sorted.io'
    params:
        running_dir = Path(config['working_dir']) / 'assembly_spades' / 'bowtie2'
    run:
        from camel.app.tools.samtools.samtoolssort import SamtoolsSort
        samtools_sort = SamtoolsSort()
        step = Step(str(rule), samtools_sort, Path(str(params.running_dir)), wildcards)
        SnakemakeUtils.add_pickle_inputs(samtools_sort, input)
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(samtools_sort, output)

rule assembly_samtools_depth:
    """
    Runs samtools depth on the BAM file of the reads mapped to the assembly.
    """
    input:
        BAM = rules.assembly_bt2_sort_bam.output.BAM
    output:
        TSV = Path(config['working_dir']) / 'assembly_spades' / 'samtools_depth' / 'tsv.io',
        INFORMS = Path(config['working_dir']) / assembly_spades.OUTPUT_ASSEMBLY_DEPTH_INFORMS
    params:
        running_dir = Path(config['working_dir']) / 'assembly_spades' / 'samtools_depth'
    run:
        from camel.app.tools.samtools.samtoolsdepth import SamtoolsDepth
        samtools_depth = SamtoolsDepth()
        step = Step(str(rule), samtools_depth, Path(str(params.running_dir)), wildcards)
        SnakemakeUtils.add_pickle_inputs(samtools_depth, input)
        step.run_step()
        samtools_depth.informs['_tag'] = 'Coverage calculation'
        SnakemakeUtils.dump_tool_outputs(samtools_depth, output)
