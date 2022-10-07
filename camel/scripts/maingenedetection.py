#!/usr/bin/env python
import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import shutil

from camel.app import loggingutils
from camel.app.utils import mainscriptutils
from camel.app.utils.preprocessing import helper_by_read_type
from camel.app.utils.report.htmlreport import HtmlReport
from camel.app.workflows.genedetectionwrapper import GeneDetectionWrapper, GeneDetectionOutput


class MainGeneDetection(object):
    """
    This class is used to run the gene detection tool.
    """

    def __init__(self, args: Optional[Sequence[str]] = None) -> None:
        """
        Initializes the main script.
        :param args: Arguments (optional)
        """
        self._args = MainGeneDetection.parse_arguments(args)
        self._sample_name = mainscriptutils.determine_sample_name(self._args)
        self._helper = helper_by_read_type[self._args.read_type](self._args.working_dir, self._sample_name)

    @staticmethod
    def parse_arguments(args: Optional[Sequence[str]]) -> argparse.Namespace:
        """
        Parses the command line arguments.
        :return: Parsed arguments
        """
        argument_parser = argparse.ArgumentParser()
        mainscriptutils.add_common_arguments(argument_parser)
        mainscriptutils.add_assembly_arguments(argument_parser)
        mainscriptutils.add_input_files_arguments(argument_parser)
        argument_parser.add_argument('--database-dir', type=Path, required=True)
        argument_parser.add_argument('--detection-method', type=str, choices=['blast', 'srst2', 'kma'], default='blast')

        # BLAST specific parameters
        argument_parser.add_argument('--output-fasta', type=Path, help='output path for assembled contigs')
        argument_parser.add_argument('--blast-min-percent-identity', type=int, default=90)
        argument_parser.add_argument('--blast-min-percent-coverage', type=int, default=60)
        argument_parser.add_argument('--blast-task', type=str, choices=['blastn', 'megablast'], default='megablast')

        # SRST2 specific parameters
        argument_parser.add_argument('--srst2-min-cov', type=int, default=90)
        argument_parser.add_argument('--srst2-max-div', type=int, default=10)
        argument_parser.add_argument('--srst2-max-unaligned-overlap', type=int, default=100)
        argument_parser.add_argument('--srst2-max-mismatch', type=int, default=10)

        # KMA specific parameters
        argument_parser.add_argument('--kma-min-percent-identity', type=int, default=90)
        argument_parser.add_argument('--kma-min-percent-coverage', type=int, default=60)
        return argument_parser.parse_args(args)

    def run(self) -> None:
        """
        Runs the main script.
        :return: None
        """
        # Initialize report
        report = mainscriptutils.init_report(
            self._args.output_html, self._args.output_dir, 'Gene detection report',
            f'Gene detection {self._args.detection_method}')
        report.add_html_object(mainscriptutils.generate_analysis_info_section(self._args))
        report.save()

        # Prepare wrapper
        wrapper = GeneDetectionWrapper(self._helper.working_dir)
        db_data = self.__get_db_metadata()

        # Run wrapper
        if self._args.detection_method == 'blast':
            fasta_input = self._helper.prepare_fasta_input(report, self._args)
            # Save assembly if specified
            if self._args.output_fasta is not None:
                shutil.copyfile(str(fasta_input), self._args.output_fasta)
            wrapper.run_workflow_blast(fasta_input, self._sample_name, db_data, self._args.threads)
        elif self._args.detection_method == 'kma':
            fastq_input = self._helper.prepare_fastq_input(report, self._args)
            wrapper.run_workflow_kma(fastq_input, self._sample_name, db_data, self._args.threads)
        elif self._args.detection_method == 'srst2':
            fastq_input = self._helper.prepare_fastq_input(report, self._args)
            wrapper.run_workflow_srst2(
                fastq_input, self._sample_name, db_data, self._args.threads)

        # Export all output
        self.__export_output(report, wrapper.output)

    def __get_db_metadata(self) -> Dict[str, Any]:
        """
        Returns the database information dictionary.
        :return: Database information dictionary
        """
        config_data = {'path': self._args.database_dir}

        # Add specific options
        if self._args.detection_method == 'blast':
            config_data.update({'params': {'blastn': {
                'min_percent_identity': self._args.blast_min_percent_identity,
                'min_coverage': self._args.blast_min_percent_coverage,
                'task': self._args.blast_task
            }}})
        elif self._args.detection_method == 'srst2':
            config_data.update({'params': {'srst2': {
                'min_coverage': self._args.srst2_min_cov,
                'max_divergence': self._args.srst2_max_div,
                'max_unaligned_overlap': self._args.srst2_max_unaligned_overlap,
                'max_mismatch': self._args.srst2_max_mismatch
            }}})
        elif self._args.detection_method == 'kma':
            config_data.update({'params': {'kma': {
                'min_percent_identity': self._args.kma_min_percent_identity,
                'min_coverage': self._args.kma_min_percent_coverage,
            }}})

        # Add extra column
        with (self._args.database_dir / 'db_metadata.txt').open() as handle:
            db_metadata = json.load(handle)
            if 'extra_column' in db_metadata:
                config_data['metadata'] = db_metadata['extra_column']
        return config_data

    def __export_output(self, report: HtmlReport, output: GeneDetectionOutput) -> None:
        """
        Exports the output of the workflow.
        :param report: HTML report
        :param output: Workflow output
        :return: None
        """
        self._helper.logs['gene_detection'] = str(output.log_file)
        self._helper.informs.append(output.informs)
        self._helper.export_output_and_commands_section(report, output.report_section)


if __name__ == '__main__':
    loggingutils.initialize_logging()
    main = MainGeneDetection()
    main.run()
