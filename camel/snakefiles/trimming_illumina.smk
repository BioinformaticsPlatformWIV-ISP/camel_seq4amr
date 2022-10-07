from pathlib import Path

from camel.app.utils.snakemake.snakemakeutils import SnakemakeUtils
from camel.app.utils.step.step import Step
from camel.snakefiles import trimming_illumina


rule trimming_illumina_fastqc_pre:
    """
    Creates FastQC reports for the raw reads. 
    """
    input:
        FASTQ = Path(config['working_dir']) / trimming_illumina.INPUT_TRIMMOMATIC_FASTQ
    output:
        HTML = Path(config['working_dir']) / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_FASTQC_HTML_PRE,
        TXT = Path(config['working_dir']) / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_FASTQC_TXT_PRE
    params:
        running_dir = Path(config['working_dir']) / 'trimming_illumina' / 'fastqc-pre'
    threads: 4
    run:
        from camel.app.tools.fastqc.fastqc import FastQC
        fastqc = FastQC()
        SnakemakeUtils.add_pickle_inputs(fastqc, input)
        step = Step(str(rule), fastqc, Path(str(params.running_dir)), wildcards)
        fastqc.update_parameters(threads=threads)
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(fastqc, output)


rule trimming_illumina_trimmomatic:
    """
    Read trimming using trimmomatic.
    """
    input:
        FASTQ_PE = Path(config['working_dir']) / trimming_illumina.INPUT_TRIMMOMATIC_FASTQ
    output:
        FASTQ_PE = Path(config['working_dir']) / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_READS_PE,
        FASTQ_SE_FORWARD = Path(config['working_dir']) / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_READS_SE_FWD,
        FASTQ_SE_REVERSE = Path(config['working_dir']) / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_READS_SE_REV,
        INFORMS = Path(config['working_dir']) / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_INFORMS
    threads: 4
    priority: 1
    params:
        running_dir = Path(config['working_dir']) / 'trimming_illumina' / 'trimmomatic',
        adapter = config.get('read_trimming', {}).get('adapter'),
        sample_name = config.get('sample_name', 'reads')
    run:
        from camel.app.tools.trimmomatic.trimmomatic import Trimmomatic
        trimmomatic = Trimmomatic()
        SnakemakeUtils.add_pickle_inputs(trimmomatic, input)
        trimmomatic.update_parameters(baseout=f'{params.sample_name}-trimmed.fastq.gz')
        if params.adapter is not None:
            trimmomatic.update_parameters(illuminaclip_PE=f'$TRIMMOMATIC_ADAPTER_DIR/{params.adapter}-PE.fa:2:30:10')
        step = Step(str(rule), trimmomatic, Path(str(params.running_dir)), wildcards)
        trimmomatic.update_parameters(threads=threads)
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(trimmomatic, output)


rule trimming_illumina_fastqc_post:
    """
    Creates FastQC reports of the trimmed reads.
    """
    input:
        FASTQ = rules.trimming_illumina_trimmomatic.output.FASTQ_PE
    output:
        HTML = Path(config['working_dir']) /  trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_FASTQC_HTML_POST,
        TXT = Path(config['working_dir']) / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_FASTQC_TXT_POST
    params:
        running_dir = Path(config['working_dir']) / 'trimming_illumina' / 'fastqc-post'
    threads: 4
    run:
        from camel.app.tools.fastqc.fastqc import FastQC
        fastqc = FastQC()
        SnakemakeUtils.add_pickle_inputs(fastqc, input)
        step = Step(str(rule), fastqc, Path(str(params.running_dir)), wildcards)
        fastqc.update_parameters(threads=threads)
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(fastqc, output)


rule trimming_illumina_report:
    """
    Creates the HTML report with the trimming output files and statistics.
    """
    input:
        HTML_PRE = rules.trimming_illumina_fastqc_pre.output.HTML,
        HTML_POST = rules.trimming_illumina_fastqc_post.output.HTML,
        FASTQ_PE = rules.trimming_illumina_trimmomatic.output.FASTQ_PE,
        FASTQ_SE_FORWARD = rules.trimming_illumina_trimmomatic.output.FASTQ_SE_FORWARD,
        FASTQ_SE_REVERSE = rules.trimming_illumina_trimmomatic.output.FASTQ_SE_REVERSE,
        INFORMS_trimming = rules.trimming_illumina_trimmomatic.output.INFORMS
    output:
        VAL_HTML = Path(config['working_dir']) / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_REPORT
    params:
        running_dir = Path(config['working_dir']) / 'trimming_illumina' / 'report',
        export_fastq = config['read_trimming'].get('export_fastq', 'false')
    run:
        from camel.app.tools.reporters.reportertrimming import ReporterTrimming
        reporter = ReporterTrimming()
        SnakemakeUtils.add_pickle_inputs(reporter, input)
        step = Step(str(rule), reporter, Path(str(params.running_dir)), wildcards)
        reporter.update_parameters(export_fastq=str(params.export_fastq))
        step.run_step()
        SnakemakeUtils.dump_tool_outputs(reporter, output)


rule trimming_illumina_dump_summary_info:
    """
    Dumps the summary information from the read trimming pipeline.
    """
    input:
        INFORMS_trimming = rules.trimming_illumina_trimmomatic.output.INFORMS
    output:
        TSV = Path(config['working_dir']) / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_SUMMARY
    params:
        running_dir = Path(config['working_dir']) / 'trimming_illumina' / 'summary'
    run:
        trimmomatic_informs = SnakemakeUtils.load_object(Path(input.INFORMS_trimming))
        summary_data = [
            ('trimming_pairs_in', trimmomatic_informs['paired_reads_in']),
            ('trimming_pairs_out', trimmomatic_informs['paired_reads_out'].split(' ')[0]),
            ('trimming_fwd_only_surviving', trimmomatic_informs['forward_only_reads'].split(' ')[0]),
            ('trimming_rev_only_surviving', trimmomatic_informs['reverse_only_reads'].split(' ')[0]),
            ('trimming_pairs_both_dropped', trimmomatic_informs['reads_drop'].split(' ')[0])
        ]
        with open(output[0], 'w') as handle:
            for key, value in summary_data:
                handle.write(f'{key}\t{value}')
                handle.write('\n')


rule trimming_illumina_to_dict:
    """
    Combines the trimmed reads into a dictionary.
    """
    input:
        FASTQ_PE = rules.trimming_illumina_trimmomatic.output.FASTQ_PE,
        FASTQ_SE_FWD = rules.trimming_illumina_trimmomatic.output.FASTQ_SE_FORWARD,
        FASTQ_SE_REV = rules.trimming_illumina_trimmomatic.output.FASTQ_SE_REVERSE
    output:
        IO = Path(config['working_dir']) / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_DICT
    run:
        output_dict = {
            'PE': SnakemakeUtils.load_object(Path(input.FASTQ_PE))
        }
        se_fwd = SnakemakeUtils.load_object(Path(input.FASTQ_SE_FWD))
        if len(se_fwd) > 0:
            output_dict['SE_FWD'] = se_fwd
        se_rev = SnakemakeUtils.load_object(Path(input.FASTQ_SE_REV))
        if len(se_rev) > 0:
            output_dict['SE_REV'] = se_rev
        SnakemakeUtils.dump_object(output_dict, Path(output.IO))
