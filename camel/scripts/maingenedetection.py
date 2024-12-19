#!/usr/bin/env python
import argparse
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from camel.app import loggingutils
from camel.app.tools.blast.blastn import Blastn
from camel.app.tools.blast.blastx import Blastx
from camel.app.utils import mainscriptutils
from camel.app.utils.report.htmlcitation import HtmlCitation
from camel.app.utils.report.htmlreport import HtmlReport
from camel.app.utils.report.htmlreportsection import HtmlReportSection
from camel.app.utils.snakemake.snakepipelineutils import SnakePipelineUtils
from camel.app.workflows.genedetectionwrapper import GeneDetectionWrapper, GeneDetectionOutput
from camel.version import __version__


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
        self._sample_name = self.__determine_sample_name()

    def __determine_sample_name(self) -> str:
        """
        Retrieves the sample name based on the input FASTA file.
        :return: Sample name
        """
        if self._args.fasta_name is not None:
            return self._args.fasta_name
        return self._args.fasta.name

    def _check_dependencies(self) -> None:
        """
        Checks if the required dependencies are available.
        :return: None
        """
        logging.info("Checking dependencies")
        tools = {'blastn': Blastn, 'blastx': Blastx}

        # Run commands to see if tools are available
        for key, Tool_class in tools.items():
            try:
                tool = Tool_class()
                logging.info(f"{tool.name}: OK (version: {tool.version})")
            except BaseException:
                raise RuntimeError(f'Dependency not found: {key}')

    @staticmethod
    def parse_arguments(args: Optional[Sequence[str]]) -> argparse.Namespace:
        """
        Parses the command line arguments.
        :return: Parsed arguments
        """
        argument_parser = argparse.ArgumentParser()

        # General arguments
        argument_parser.add_argument('--sample-name', type=str, help='Dataset name (will be determined from the input if not specified)')
        argument_parser.add_argument('--output-dir', required=True, type=Path, help='Output directory')
        argument_parser.add_argument('--output-html', type=Path, help='Output HTML report')
        argument_parser.add_argument('--working-dir', default=Path.cwd(), type=Path, help='Working directory for temporary files')
        argument_parser.add_argument('--threads', default=8, type=int, help='Number of threads to use')

        # Input files
        argument_parser.add_argument('--fasta', help='Input FASTA file', type=Path, required=True)
        argument_parser.add_argument('--fasta-name', help='Input FASTA file name', type=str)
        argument_parser.add_argument('--database-dir', type=Path, required=True, help='Input database directory')

        # BLAST-specific parameters
        argument_parser.add_argument('--blast-min-percent-identity', type=int, default=90, help='Minimum percent identity')
        argument_parser.add_argument('--blast-min-percent-coverage', type=int, default=60, help='Minimum percent target coverage')
        argument_parser.add_argument('--blast-task', type=str, choices=['blastn', 'megablast'], default='megablast', help="Value of the blast '-task' parameter")

        # Version
        argument_parser.add_argument(
            '--version', help='Print version and exit', action='version', version=f'Gene detection {__version__}')
        return argument_parser.parse_args(args)

    def run(self) -> None:
        """
        Runs the main script.
        :return: None
        """
        logging.info(f'Running gene detection on: {self._sample_name}')
        self._check_dependencies()

        # Symlink the input (if needed)
        if self._args.fasta_name is not None:
            path_symlink = Path(
                self._args.working_dir, 'input', mainscriptutils.sanitize_input_name(self._sample_name, 'fasta'))
            path_symlink.parent.mkdir(parents=True, exist_ok=True)
            path_symlink.symlink_to(self._args.fasta)
            self._args.fasta = path_symlink

        # Initialize the report
        if self._args.output_html is None:
            self._args.output_html = self._args.output_dir / 'report.html'
        report = mainscriptutils.init_report(
            self._args.output_html, self._args.output_dir, 'Gene detection report','Gene detection')
        report.add_html_object(mainscriptutils.generate_analysis_info_section(self._args))
        report.save()

        # Prepare wrapper
        wrapper = GeneDetectionWrapper(self._args.working_dir)
        db_data = self.__get_db_metadata()

        # Run wrapper
        wrapper.run_workflow_blast(self._args.fasta, self._sample_name, db_data, self._args.threads)

        # Export all output
        self.__export_output(report, wrapper.output)

    def __get_db_metadata(self) -> Dict[str, Any]:
        """
        Returns the database information dictionary.
        :return: Database information dictionary
        """
        config_data = {'path': str(self._args.database_dir)}

        # Add specific options
        config_data.update({'params': {'blastn': {
            'min_percent_identity': self._args.blast_min_percent_identity,
            'min_coverage': self._args.blast_min_percent_coverage,
            'task': self._args.blast_task
        }}})
        return config_data

    def __export_output(self, report: HtmlReport, output: GeneDetectionOutput) -> None:
        """
        Exports the output of the workflow.
        :param report: HTML report
        :param output: Workflow output
        :return: None
        """
        report.add_html_object(output.report_section)
        output.report_section.copy_files(report.output_dir)

        # Commands
        section_commands = SnakePipelineUtils.create_commands_section(
            [output.informs], self._args.working_dir)
        report.add_html_object(section_commands)

        # Citations
        section_citations = HtmlReportSection('Citations')
        section_citations.add_header('Tools and databases', 3)
        for citation_key in ['Bogaerts_2019-neisseria_validation', 'Camacho_2009-blast']:
            section_citations.add_html_object(HtmlCitation.parse_from_json(citation_key))
        report.add_html_object(section_citations)
        report.save()
        logging.info(f'Report saved to: {self._args.output_html}')


if __name__ == '__main__':
    loggingutils.initialize_logging()
    main = MainGeneDetection()
    main.run()
