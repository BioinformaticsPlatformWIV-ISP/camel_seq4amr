import argparse
import logging
from pathlib import Path
from typing import List

from camel.app.io.tooliofile import ToolIOFile
from camel.app.utils.fastqinput import FastqInput
from camel.app.utils.fileutils import FileUtils
from camel.app.utils.preprocessing.basereadtypehelper import BaseReadTypeHelper
from camel.app.utils.report.htmlreport import HtmlReport
from camel.app.workflows.trimmingilluminawrapper import TrimmingIlluminaWrapper


class IlluminaHelper(BaseReadTypeHelper):
    """
    Helper class for Illumina reads.
    """

    def __symlink_fastq_files(self, fastq_files: List[Path], sample_name: str) -> List[Path]:
        """
        Symlinks the input files to a standardized format based on the sample name.
        :param fastq_files: Input FASTQ files
        :param sample_name: Sample name
        :return: Path to renamed files
        """
        new_filenames = []
        for orientation, fastq_file in enumerate(fastq_files, 1):
            is_gzipped = FileUtils.is_gzipped(fastq_file)
            extension = 'fastq.gz' if is_gzipped else 'fastq'
            new_filenames.append(f"{sample_name}_{orientation}.{extension}")
        return self.symlink_input_files([Path(x) for x in fastq_files], new_filenames)

    def trim_reads(self, fastq_input: FastqInput, report: HtmlReport, include_fastq: bool = False, threads: int = 4,
                   **kwargs) -> FastqInput:
        """
        Trims Illumina reads using Trimmomatic.
        :param fastq_input: FASTQ input
        :param report: HTML report
        :param include_fastq: Boolean to indicate if FASTQ files should be included in the report
        :param threads: Nb. of threads
        :return: FastqInput object with trimmed reads
        """
        logging.info("Trimming reads (Illumina data)")
        trimming = TrimmingIlluminaWrapper(self._working_dir / 'trimming')
        if (not fastq_input.is_pe) or (fastq_input.pe is None):
            raise ValueError("Illumina FASTQ input should be paired")

        # Run workflow
        trimming.run_workflow([Path(x.path) for x in fastq_input.pe], kwargs.get('adapter'), threads, include_fastq)

        # Save output
        report_section_trimming = trimming.output.report_section
        report.add_html_object(report_section_trimming)
        report_section_trimming.copy_files(report.output_dir)
        self._informs.append(trimming.output.informs_trimmomatic)
        self._log_files['trimming'] = trimming.output.log_file
        return FastqInput('illumina', trimming.output.trimmed_reads_pe, se_fwd=trimming.output.trimmed_reads_se_fwd,
                          se_rev=trimming.output.trimmed_reads_se_rev)

    def prepare_fasta_input(self, report: HtmlReport, args: argparse.Namespace) -> Path:
        """
        Prepares the FASTA input.
        :param report: HTML report
        :param args: Command-line arguments
        :return: FASTA file
        """
        logging.info("Preparing FASTA input (Illumina data)")
        if args.fasta is not None:
            fasta_file = self.symlink_input_files([Path(args.fasta)], [args.fasta_name])[0]
            return Path(fasta_file)
        fq_input_pe = self.__symlink_fastq_files([Path(x) for x in args.fastq_pe], self._sample_name)
        fastq_input = FastqInput('illumina', pe=[ToolIOFile(x) for x in fq_input_pe])
        if args.trim_reads:
            assembly_input = self.trim_reads(
                fastq_input, report, args.report_include_fastq, args.threads, adapter=args.adapter)
        else:
            assembly_input = FastqInput('illumina', pe=[ToolIOFile(in_file) for in_file in fq_input_pe])
        return self.assemble_fastq_reads(assembly_input, args, report)

    def prepare_fastq_input(self, report: HtmlReport, args: argparse.Namespace) -> FastqInput:
        """
        Prepares the FASTQ input.
        :param report: HTML report
        :param args: Command-line arguments
        :return: FASTQ input
        """
        fq_input_pe = self.__symlink_fastq_files([Path(x) for x in args.fastq_pe], self._sample_name)
        fastq_input = FastqInput('illumina', pe=[ToolIOFile(x) for x in fq_input_pe])
        if args.trim_reads:
            return self.trim_reads(fastq_input, report, args.report_include_fastq, args.threads, adapter=args.adapter)
        else:
            return FastqInput('illumina', pe=[ToolIOFile(in_file) for in_file in fq_input_pe])
