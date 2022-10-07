from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

from camel.app.utils.fastqinput import FastqInput
from camel.app.utils.report.htmlreportsection import HtmlReportSection
from camel.app.utils.snakemake.snakemakeutils import SnakemakeUtils
from camel.app.utils.snakemake.snakepipelineutils import SnakePipelineUtils
from camel.snakefiles import assembly_spades


@dataclass
class AssemblyOutput:
    report_section: HtmlReportSection
    tsv_summary: Path
    fasta_contigs: Path
    log_file: Optional[Path]
    informs: List[Dict[str, Any]]
    qc_stats: Optional[Dict[str, Any]] = None


class AssemblyWrapper(object):
    """
    This class is used as a wrapper class around the assembly Snakemake workflow.
    """

    def __init__(self, working_dir: Path) -> None:
        """
        Initializes the read trimming helper.
        :param working_dir: Working directory
        """
        self._working_dir = working_dir
        self._working_dir.mkdir(parents=True, exist_ok=True)
        self._output = None

    def run(
            self, sample_name: str, fastq_input: FastqInput, kmers: str = None,
            cov_cutoff: Union[str, int] = 'off', min_contig_length: Optional[int] = None, calc_qc_stats: bool = False,
            threads: int = 8) -> None:
        """
        Runs the assembly workflow for paired-end input.
        :param fastq_input: FASTQ input
        :param sample_name: Sample name
        :param kmers: Comma separated list of kmer sizes to use for assembly
        :param cov_cutoff: Coverage cutoff
        :param min_contig_length: Minimum contig length
        :param calc_qc_stats: If True, determines the QC stats
        :param threads: Number of threads
        :return: None
        """
        if fastq_input.is_pe:
            fq_dict = {'PE': fastq_input.pe}
            if fastq_input.se_fwd is not None:
                fq_dict['SE_FWD'] = fastq_input.se_fwd
            if fastq_input.se_rev is not None:
                fq_dict['SE_REV'] = fastq_input.se_rev
        else:
            fq_dict = {'SE': fastq_input.se}
        SnakemakeUtils.dump_object(fq_dict, self._working_dir / 'fq_dict.io')
        self.__run_workflow(
            sample_name, kmers, cov_cutoff, min_contig_length, fastq_input.read_type, calc_qc_stats, threads)

    def __run_workflow(
            self, sample_name: str, kmers: str = None, cov_cutoff: Union[str, int] = 'off',
            min_contig_length: Optional[int] = None, read_type: str = 'illumina', calc_qc_stats: bool = False,
            threads: int = 8) -> None:
        """
        Runs the underlying workflow.
        :return: None
        """
        if not self._working_dir.exists():
            self._working_dir.mkdir(parents=True)
        config_data = self.__get_config_data(sample_name, kmers, cov_cutoff, min_contig_length, read_type)
        config_file = SnakePipelineUtils.generate_config_file(config_data, self._working_dir)
        output_files = self.__get_output_files_dict(min_contig_length, calc_qc_stats)
        SnakePipelineUtils.run_snakemake(
            assembly_spades.SNAKEFILE_ASSEMBLY_SPADES, config_file, list(output_files.values()),
            Path(self._working_dir), threads)
        self.__set_output(output_files)

    def __get_output_files_dict(self, min_contig_length: Union[int, None], calc_qc_stats: bool) -> Dict[str, Path]:
        """
        Returns the dictionary with output files.
        :return: Dictionary with output files.
        """
        output_files = {
            'HTML': self._working_dir / assembly_spades.OUTPUT_ASSEMBLY_REPORT,
            'TSV': self._working_dir / assembly_spades.OUTPUT_ASSEMBLY_SUMMARY,
            'FASTA': self._working_dir / assembly_spades.OUTPUT_ASSEMBLY_FASTA,
            'INFORMS_spades': self._working_dir / assembly_spades.OUTPUT_ASSEMBLY_INFORMS
        }
        if calc_qc_stats is True:
            output_files['INFORMS_bowtie2'] = self._working_dir / assembly_spades.OUTPUT_ASSEMBLY_MAPPING_INFORMS
            output_files['INFORMS_samtools'] = self._working_dir / assembly_spades.OUTPUT_ASSEMBLY_DEPTH_INFORMS
        if min_contig_length is not None:
            output_files['INFORMS_seqtk'] = self._working_dir / assembly_spades.OUTPUT_ASSEMBLY_FILTERING_INFORMS
        return output_files

    def __get_config_data(self, sample_name: str, kmers: str, cov_cutoff: Union[int, str],
                          min_contig_length: Optional[int] = None, read_type: str = 'illumina') -> Dict[str, Any]:
        """
        Builds the configuration file to run the assembly workflow.
        :param sample_name: Sample name
        :param kmers: Comma separated list of Kmer sizes to use for the assembly
        :param cov_cutoff: Coverage cutoff
        :return: Config data
        """
        config_data = {
            'sample_name': sample_name,
            'working_dir': self._working_dir,
            'assembly': {'spades': {}},
            'read_type': read_type
        }

        # SPAdes options
        if kmers is not None:
            config_data['assembly']['spades']['kmers'] = kmers
        if cov_cutoff is not None:
            config_data['assembly']['spades']['cov_cutoff'] = cov_cutoff
        if read_type == 'iontorrent':
            config_data['assembly']['spades']['iontorrent'] = None

        # Length filtering
        if min_contig_length is not None:
            # noinspection PyTypeChecker
            config_data['assembly']['min_contig_length'] = min_contig_length

        return config_data

    def __set_output(self, output_files: Dict[str, Path]) -> None:
        """
        Runs the Snakemake workflow.
        :param output_files: Output files dictionary
        :return: None
        """
        log_file_path = self._working_dir / 'camel.log'
        informs = [SnakemakeUtils.load_object(output_files['INFORMS_spades'])]
        if 'INFORMS_seqtk' in output_files:
            informs.append(SnakemakeUtils.load_object(output_files['INFORMS_seqtk']))
        if all(key in output_files for key in ('INFORMS_bowtie2', 'INFORMS_samtools')):
            qc_stats = {
                'depth': SnakemakeUtils.load_object(output_files['INFORMS_samtools']),
                'mapping': SnakemakeUtils.load_object(output_files['INFORMS_bowtie2']),
            }
        else:
            qc_stats = None
        self._output = AssemblyOutput(
            report_section=SnakemakeUtils.load_object(output_files['HTML'])[0].value,
            tsv_summary=output_files['TSV'],
            fasta_contigs=SnakemakeUtils.load_object(output_files['FASTA'])[0].path,
            informs=informs,
            log_file=log_file_path if log_file_path.exists() else None,
            qc_stats=qc_stats
        )

    @property
    def output(self) -> AssemblyOutput:
        """
        Returns the output of the assembly workflow.
        :return: Assembly output
        """
        return self._output
