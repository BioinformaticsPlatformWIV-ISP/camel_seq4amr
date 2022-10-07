import argparse
import logging
from pathlib import Path
from typing import Union

from camel.app.io.tooliofile import ToolIOFile
from camel.app.utils.fastqinput import FastqInput
from camel.app.utils.fileutils import FileUtils
from camel.app.utils.preprocessing.basereadtypehelper import BaseReadTypeHelper
from camel.app.utils.report.htmlreport import HtmlReport
from camel.app.workflows.trimmingiontorrentwrapper import TrimmingIonTorrentWrapper


class IonTorrentHelper(BaseReadTypeHelper):
    """
    Helper class for IonTorrent reads.
    """

    def __symlink_iontorrent_reads(self, fastq_file: Union[Path, None], sample_name: str) -> Path:
        """
        Symlinks the input files to a standardized format based on the sample name.
        :param fastq_file: Input FASTQ file
        :param sample_name: Sample name
        :return: Path to renamed file
        """
        if fastq_file is None:
            raise ValueError("IonTorrent data should be SE")
        new_name = f"{sample_name}.fastq{'.gz' if FileUtils.is_gzipped(fastq_file) else ''}"
        return self.symlink_input_files([Path(fastq_file)], [new_name])[0]

    def trim_reads(self, fastq_input: FastqInput, report: HtmlReport, include_fastq: bool, threads: int = 4,
                   **kwargs) -> FastqInput:
        """
        Trims IonTorrent reads using .
        :param fastq_input: FASTQ input
        :param report: HTML report
        :param include_fastq: Boolean to indicate if FASTQ files should be included in the report
        :param threads: Nb. of threads
        :return: FastqInput object with trimmed reads
        """
        logging.info("Trimming reads (IonTorrent data)")
        if fastq_input.is_pe or fastq_input.se is None:
            raise ValueError("IonTorrent input should be SE")
        # Run workflow
        trimming = TrimmingIonTorrentWrapper(self._working_dir / 'trimming')
        if fastq_input.is_pe:
            raise ValueError("PE data not allowed for IonTorrent")
        trimming.run_workflow(Path(fastq_input.se[0].path), include_fastq, threads)

        # Save output
        report_section_trimming = trimming.output.report_section
        report.add_html_object(report_section_trimming)
        report_section_trimming.copy_files(report.output_dir)
        self._informs.extend(trimming.output.informs_seqtk)
        self._log_files['trimming'] = trimming.output.log_file
        return FastqInput('iontorrent', se=trimming.output.trimmed_reads, is_pe=False)

    def prepare_fasta_input(self, report: HtmlReport, args: argparse.Namespace) -> Path:
        """
        Prepares the FASTA input.
        :param report: HTML report
        :param args: Command-line arguments
        :return: FASTA file
        """
        logging.info("Preparing FASTA input (IonTorrent data)")
        fq_input_se = self.__symlink_iontorrent_reads(Path(args.fastq_se), self._sample_name)
        fastq_input = FastqInput(args.read_type, se=[ToolIOFile(fq_input_se)], is_pe=False)
        if args.trim_reads:
            assembly_input = self.trim_reads(fastq_input, report, args.report_include_fastq, args.threads)
        else:
            assembly_input = fastq_input
        return self.assemble_fastq_reads(assembly_input, args, report)

    def prepare_fastq_input(self, report: HtmlReport, args: argparse.Namespace) -> FastqInput:
        """
        Prepares the FASTQ input.
        :param report: HTML report
        :param args: Command-line arguments
        :return: FASTQ input
        """
        fq_input_se = self.__symlink_iontorrent_reads(Path(args.fastq_se), self._sample_name)
        fastq_input = FastqInput(args.read_type, se=[ToolIOFile(fq_input_se)], is_pe=False)
        if args.trim_reads:
            return self.trim_reads(fastq_input, report, args.report_include_fastq, args.threads)
        else:
            return FastqInput(args.read_type, se=[ToolIOFile(fq_input_se)], is_pe=False)
