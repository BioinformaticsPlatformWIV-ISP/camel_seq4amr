from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from camel.app.io.tooliofile import ToolIOFile
from camel.app.utils.report.htmlreportsection import HtmlReportSection
from camel.app.utils.snakemake.snakemakeutils import SnakemakeUtils
from camel.app.utils.snakemake.snakepipelineutils import SnakePipelineUtils
from camel.snakefiles import trimming_iontorrent


class TrimmingIonTorrentWrapper(object):
    """
    This class is used as a wrapper class around the IonTorrent read trimming Snakemake workflow.
    """

    @dataclass
    class ReadTrimmingOutput:
        report_section: HtmlReportSection
        tsv_summary: Path
        trimmed_reads: List[ToolIOFile]
        informs_seqtk: List[Dict[str, Any]]
        log_file: Optional[Path] = None

    def __init__(self, working_dir: Path) -> None:
        """
        Initializes the read trimming wrapper.
        :param working_dir: Working directory
        """
        self._working_dir = Path(working_dir)
        self._output = None

    def run_workflow(self, se_reads: Path, export_fastq: bool = False, threads: int = 8) -> None:
        """
        Runs the read trimming workflow.
        :param se_reads: Input SE FASTQ reads
        :param threads: Number of threads to use
        :param export_fastq: If True, FASTQ files are included in the report
        :return: None
        """
        config_data = {
            'working_dir': str(self._working_dir),
            'input': {'fastq_se': [{'name': se_reads.name, 'path': str(se_reads)}]},
            'read_trimming': {'export_fastq': str(export_fastq)},
            'read_type': 'iontorrent'
        }
        config_file = SnakePipelineUtils.generate_config_file(config_data, self._working_dir)
        output_files = {
            'HTML': self._working_dir / trimming_iontorrent.OUTPUT_TRIMMING_IONTORRENT_REPORT,
            'TSV': self._working_dir / trimming_iontorrent.OUTPUT_TRIMMING_IONTORRENT_SUMMARY,
            'INFORMS_seqtk_len': self._working_dir / trimming_iontorrent.OUTPUT_TRIMMING_IONTORRENT_INFORMS_FILT_LEN,
            'INFORMS_seqtk_qual': self._working_dir / trimming_iontorrent.OUTPUT_TRIMMING_IONTORRENT_INFORMS_FILT_QUAL,
        }
        SnakePipelineUtils.run_snakemake(
            trimming_iontorrent.SNAKEFILE_TRIMMING_IONTORRENT, config_file, list(output_files.values()),
            self._working_dir, threads)
        self.__set_output(output_files)

    def __set_output(self, output_files: Dict[str, Path]) -> None:
        """
        Sets the output of this tool.
        :param output_files: Output files by key.
        :return: None
        """
        log_path = self._working_dir / 'camel.log'
        informs_seqtk = [SnakemakeUtils.load_object(
            output_files[key]) for key in ('INFORMS_seqtk_len', 'INFORMS_seqtk_qual')]
        self._output = TrimmingIonTorrentWrapper.ReadTrimmingOutput(
            report_section=SnakemakeUtils.load_object(output_files['HTML'])[0].value,
            tsv_summary=output_files['TSV'],
            trimmed_reads=SnakemakeUtils.load_object(
                self._working_dir / trimming_iontorrent.OUTPUT_TRIMMING_IONTORRENT_FASTQ),
            informs_seqtk=informs_seqtk,
            log_file=log_path if log_path.exists() else None
        )

    @property
    def output(self) -> 'TrimmingIonTorrentWrapper.ReadTrimmingOutput':
        """
        Returns the report section generated during the read trimming pipeline.
        :return: Trimming section
        """
        return self._output
