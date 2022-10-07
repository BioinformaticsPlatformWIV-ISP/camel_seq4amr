import argparse
from pathlib import Path
from typing import Union

from camel.app.io.tooliofile import ToolIOFile
from camel.app.utils.fastqinput import FastqInput
from camel.app.utils.fileutils import FileUtils
from camel.app.utils.preprocessing.basereadtypehelper import BaseReadTypeHelper
from camel.app.utils.report.htmlreport import HtmlReport


class NanoporeHelper(BaseReadTypeHelper):
    """
    Helper class for Nanopore reads.
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
        Trims Illumina reads using Trimmomatic.
        :param fastq_input: FASTQ input
        :param report: HTML report
        :param include_fastq: Boolean to indicate if FASTQ files should be included in the report
        :param threads: Nb. of threads
        :return: FastqInput object with trimmed reads
        """
        raise NotImplementedError("Trimming for Nanopore data is currently not supported")

    def prepare_fasta_input(self, report: HtmlReport, args: argparse.Namespace) -> Path:
        """
        Prepares the FASTA input.
        :param report: HTML report
        :param args: Command-line arguments
        :return: FASTA file
        """
        raise NotImplementedError("Assembly for Nanopore data is currently not supported.")

    def prepare_fastq_input(self, report: HtmlReport, args: argparse.Namespace) -> FastqInput:
        """
        Prepares the FASTQ input.
        :param report: HTML report
        :param args: Command-line arguments
        :return: FASTQ input
        """
        fq_input_se = self.__symlink_iontorrent_reads(Path(args.fastq_se), self._sample_name)
        fastq_input = FastqInput(args.read_type, se=[ToolIOFile(Path(fq_input_se))], is_pe=False)
        if args.trim_reads:
            return self.trim_reads(fastq_input, report, args.report_include_fastq, args.threads)
        else:
            return FastqInput(args.read_type, se=[ToolIOFile(Path(fq_input_se))], is_pe=False)
