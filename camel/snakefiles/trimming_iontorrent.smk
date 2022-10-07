from pathlib import Path

from camel.app.utils.snakemake.snakemakeutils import SnakemakeUtils
from camel.app.utils.step.step import Step
from camel.snakefiles import trimming_iontorrent


rule trimming_iontorrent_pickle_fastq_input:
    """
    Creates a pickle for the fastq input files. 
    If downsampling is enabled the input is retrieved from the corresponding Snakefile. Otherwise, the input files are
    obtained from the Snakemake config.
    """
    output:
        FASTQ_SE = Path(config['working_dir']) / 'trimming_iontorrent' / 'input' / 'fastq-se.io'
    params:
        config_input = config['input']
    run:
        from camel.app.utils.command import Command
        from camel.app.io.tooliofile import ToolIOFile
        from camel.app.utils.fileutils import FileUtils
        from camel.app.error.pipelineexecutionerror import PipelineExecutionError

        # Get the FASTQ file
        fastq_se_in = Path(config['input']['fastq_se'][0]['path'])

        # Unzip the FASTQ file if it is compressed
        if FileUtils.is_gzipped(fastq_se_in):
            path_out = Path(output.FASTQ_SE).parent / fastq_se_in.name.replace('.gz', '')
            command = Command(f'gunzip -c {fastq_se_in} > {path_out}')
            command.run(path_out.parent)
            if not command.returncode == 0:
                raise PipelineExecutionError(f"Cannot unzip input file: {command.stderr}")
            SnakemakeUtils.dump_object([ToolIOFile(path_out)], Path(output.FASTQ_SE))
        else:
            SnakemakeUtils.dump_object([ToolIOFile(fastq_se_in)], Path(output.FASTQ_SE))

rule trimming_iontorrent_fastqc_pre:
    """
    Creates FastQC reports for the raw reads. 
    """
    input:
        FASTQ = rules.trimming_iontorrent_pickle_fastq_input.output.FASTQ_SE
    output:
        HTML = Path(config['working_dir']) / 'trimming_iontorrent' / 'fastqc-pre' / 'html.io',
        TXT = Path(config['working_dir']) / trimming_iontorrent.OUTPUT_TRIMMING_IONTORRENT_FASTQC_PRE
    params:
        running_dir = Path(config['working_dir']) / 'trimming_iontorrent' /'fastqc-pre'
    run:
        from camel.app.tools.fastqc.fastqc import FastQC
        fastqc = FastQC()
        SnakemakeUtils.add_pickle_inputs(fastqc, input)
        step = Step(str(rule), fastqc, Path(str(params.running_dir)))
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(fastqc, output)


rule trimming_iontorrent_filter_length:
    """
    Filters input reads based on read length.
    """
    input:
        FASTQ = rules.trimming_iontorrent_pickle_fastq_input.output.FASTQ_SE
    output:
        FASTQ = Path(config['working_dir']) / 'trimming_iontorrent' / 'trim_length' / 'fastq.io',
        INFORMS = Path(config['working_dir']) / 'trimming_iontorrent' / 'trim_length' / 'informs.io'
    params:
        running_dir = Path(config['working_dir']) / 'trimming_iontorrent' / 'trim_length'
    run:
        from camel.app.tools.fastx.fastqqualitytrimmer import FastqQualityTrimmer
        trimmer = FastqQualityTrimmer()
        SnakemakeUtils.add_pickle_inputs(trimmer, input)
        step = Step(str(rule),trimmer, Path(str(params.running_dir)))
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(trimmer, output)


rule trimming_iontorrent_filter_quality:
    """
    Filters input reads based on quality score.
    """
    input:
        FASTQ = rules.trimming_iontorrent_filter_length.output.FASTQ
    output:
        FASTQ = Path(config['working_dir']) / trimming_iontorrent.OUTPUT_TRIMMING_IONTORRENT_FASTQ,
        INFORMS = Path(config['working_dir']) / 'trimming_iontorrent' / 'trim_qual' / 'informs.io'
    params:
        running_dir = Path(config['working_dir']) / 'trimming_iontorrent' / 'trim_qual'
    run:
        from camel.app.tools.fastx.fastqqualityfilter import FastqQualityFilter
        q_filter = FastqQualityFilter()
        SnakemakeUtils.add_pickle_inputs(q_filter , input)
        step = Step(str(rule),q_filter, Path(str(params.running_dir)))
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(q_filter, output)


rule trimming_iontorrent_fastqc_post:
    """
    Creates FastQC reports of the filtered reads.
    """
    input:
        FASTQ = rules.trimming_iontorrent_filter_quality.output.FASTQ
    output:
        HTML = Path(config['working_dir']) / 'trimming_iontorrent' / 'fastqc-post' / 'html.io',
        TXT = Path(config['working_dir']) / trimming_iontorrent.OUTPUT_TRIMMING_IONTORRENT_FASTQC_POST
    params:
        running_dir = Path(config['working_dir']) / 'trimming_iontorrent' /'fastqc-post'
    run:
        from camel.app.tools.fastqc.fastqc import FastQC
        fastqc = FastQC()
        SnakemakeUtils.add_pickle_inputs(fastqc, input)
        step = Step(str(rule), fastqc, Path(str(params.running_dir)))
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(fastqc, output)


rule trimming_iontorrent_report:
    """
    Creates the HTML report with the trimming output files and statistics.
    """
    input:
        HTML_PRE = rules.trimming_iontorrent_fastqc_pre.output.HTML,
        HTML_POST = rules.trimming_iontorrent_fastqc_post.output.HTML,
        FASTQ = rules.trimming_iontorrent_filter_quality.output.FASTQ,
        INFORMS_filt_len = rules.trimming_iontorrent_filter_length.output.INFORMS,
        INFORMS_filt_qual = rules.trimming_iontorrent_filter_quality.output.INFORMS
    output:
        VAL_HTML = Path(config['working_dir']) / trimming_iontorrent.OUTPUT_TRIMMING_IONTORRENT_REPORT
    params:
        running_dir = Path(config['working_dir']) / 'trimming_iontorrent' / 'report'
    run:
        from camel.app.tools.reporters.reportertrimmingiontorrent import ReporterTrimmingIonTorrent
        reporter = ReporterTrimmingIonTorrent()
        SnakemakeUtils.add_pickle_inputs(reporter, input)
        step = Step(str(rule), reporter, Path(str(params.running_dir)))
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(reporter, output)


rule trimming_iontorrent_dump_summary_info:
    """
    Collects the summary information for the IonTorrent read trimming.
    """
    input:
        INFORMS_filt_len = rules.trimming_iontorrent_filter_length.output.INFORMS,
        INFORMS_filt_qual = rules.trimming_iontorrent_filter_quality.output.INFORMS
    output:
        TSV = Path(config['working_dir']) / trimming_iontorrent.OUTPUT_TRIMMING_IONTORRENT_SUMMARY
    run:
        informs_len = SnakemakeUtils.load_object(Path(input.INFORMS_filt_len))
        informs_qual = SnakemakeUtils.load_object(Path(input.INFORMS_filt_qual))
        with open(output[0], 'w') as handle:
            for k, v in [
                ('filt_len_in', informs_len['input_reads']),
                ('filt_len_out', informs_len['output_reads']),
                ('filt_qual_in', informs_qual['input_reads']),
                ('filt_qual_out', informs_qual['output_reads'])]:
                handle.write('\t'.join([k, str(v)]))
                handle.write('\n')


rule trimming_iontorrent_to_dict:
    """
    Combines the trimmed reads into a standardized dictionary.
    """
    input:
        FASTQ = rules.trimming_iontorrent_filter_quality.output.FASTQ
    output:
        IO = Path(config['working_dir']) / trimming_iontorrent.OUTPUT_TRIMMING_IONTORRENT_DICT
    run:
        output_dict = {
            'SE': SnakemakeUtils.load_object(Path(input.FASTQ))
        }
        SnakemakeUtils.dump_object(output_dict, Path(output.IO))
