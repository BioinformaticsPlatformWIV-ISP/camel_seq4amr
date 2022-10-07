from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from camel.app.io.tooliofile import ToolIOFile
from camel.app.utils.report.htmlreportsection import HtmlReportSection
from camel.app.utils.snakemake.snakemakeutils import SnakemakeUtils
from camel.app.utils.snakemake.snakepipelineutils import SnakePipelineUtils
from camel.snakefiles import trimming_illumina


class TrimmingIlluminaWrapper(object):
    """
    This class is used as a wrapper class around the Illumina read trimming Snakemake workflow.
    """

    @dataclass
    class ReadTrimmingOutput:
        report_section: HtmlReportSection
        tsv_summary: Path
        trimmed_reads_pe: List[ToolIOFile]
        trimmed_reads_se_fwd: List[ToolIOFile]
        trimmed_reads_se_rev: List[ToolIOFile]
        informs_trimmomatic: Dict[str, Any]
        fastq_reports_pre: List[ToolIOFile]
        fastq_reports_post: List[ToolIOFile]
        log_file: Optional[Path] = None

    def __init__(self, working_dir: Path) -> None:
        """
        Initializes the read trimming wrapper.
        :param working_dir: Working directory
        """
        self._working_dir = Path(working_dir)
        self._output = None

    def run_workflow(self, pe_reads: List[Path], adapter: Optional[str] = None, threads: int = 8,
                     export_fastq: bool = False) -> None:
        """
        Runs the read trimming workflow.
        :param pe_reads: Input PE FASTQ reads
        :param adapter: Adapter to trim
        :param threads: Number of threads to use
        :param export_fastq: If True, FASTQ files are included in the report
        :return: None
        """
        # Create config file
        config_data = {
            'working_dir': str(self._working_dir),
            'input': {'fastq_pe': [{'name': p.name, 'path': str(p)} for p in pe_reads]},
            'read_trimming': {'export_fastq': str(export_fastq)}
        }
        if adapter is not None:
            config_data['read_trimming']['adapter'] = adapter
        config_file = SnakePipelineUtils.generate_config_file(config_data, self._working_dir)

        # Dump the input files in an IO file
        io_pickle_in = Path(self._working_dir / trimming_illumina.INPUT_TRIMMOMATIC_FASTQ)
        io_pickle_in.parent.mkdir(exist_ok=True, parents=True)
        SnakemakeUtils.dump_object([ToolIOFile(x) for x in pe_reads], io_pickle_in)

        # Output files
        output_files = {
            'HTML': self._working_dir / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_REPORT,
            'TSV': self._working_dir / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_SUMMARY
        }
        SnakePipelineUtils.run_snakemake(
            trimming_illumina.SNAKEFILE_TRIMMING_ILLUMINA, config_file, list(output_files.values()), self._working_dir,
            threads)
        self.__set_output(output_files)

    def __set_output(self, output_files: Dict[str, Path]) -> None:
        """
        Sets the output of this tool.
        :param output_files: Output files by key.
        :return: None
        """
        log_path = self._working_dir / 'camel.log'
        self._output = TrimmingIlluminaWrapper.ReadTrimmingOutput(
            report_section=SnakemakeUtils.load_object(output_files['HTML'])[0].value,
            tsv_summary=output_files['TSV'],
            trimmed_reads_pe=SnakemakeUtils.load_object(
                self._working_dir / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_READS_PE),
            trimmed_reads_se_fwd=SnakemakeUtils.load_object(
                self._working_dir / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_READS_SE_FWD),
            trimmed_reads_se_rev=SnakemakeUtils.load_object(
                self._working_dir / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_READS_SE_REV),
            informs_trimmomatic=SnakemakeUtils.load_object(
                self._working_dir / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_INFORMS),
            fastq_reports_pre=SnakemakeUtils.load_object(
                self._working_dir / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_FASTQC_HTML_PRE),
            fastq_reports_post=SnakemakeUtils.load_object(
                self._working_dir / trimming_illumina.OUTPUT_TRIMMING_ILLUMINA_FASTQC_HTML_POST),
            log_file=log_path if log_path.exists() else None
        )

    @property
    def output(self) -> 'TrimmingIlluminaWrapper.ReadTrimmingOutput':
        """
        Returns the report section generated during the read trimming pipeline.
        :return: Trimming section
        """
        return self._output
