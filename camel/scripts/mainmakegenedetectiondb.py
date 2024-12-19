#!/usr/bin/env python
import argparse
import logging
import shutil
from importlib.resources import files
from pathlib import Path
from typing import Optional, Sequence

from camel.app import loggingutils
from camel.app.tools.blast.makeblastdb import MakeBlastDb
from camel.app.tools.cdhit.cdhitest import CDHitEst
from camel.app.utils import mainscriptutils
from camel.app.utils.genedetection.dbhelper import DBHelper
from camel.app.utils.genedetection.genedetectionutils import GeneDetectionUtils
from camel.app.utils.report.htmlreport import HtmlReport
from camel.app.utils.report.htmlreportsection import HtmlReportSection
from camel.app.utils.snakemake.snakepipelineutils import SnakePipelineUtils


class MainMakeGeneDetectionDB(object):
    """
    This class is used to create databases for the gene detection tool.
    """

    def __init__(self, args: Optional[Sequence[str]] = None) -> None:
        """
        Initializes this tool.
        :param args: (Optional) arguments
        """
        self._args = MainMakeGeneDetectionDB.parse_arguments(args)
        fasta_name = self._args.fasta_name if self._args.fasta_name is not None else self._args.fasta.name
        self._db_name = mainscriptutils.sanitize_input_name(fasta_name, 'fasta')
        self._helper = DBHelper(self._db_name, self._args.working_dir)
        self._clusters = None
        self._new_name_by_header = None

    def _check_dependencies(self) -> None:
        """
        Checks if the required dependencies are available.
        :return: None
        """
        logging.info("Checking dependencies")
        tools = {'blast': MakeBlastDb, 'CD-HIT': CDHitEst}

        # Run commands to see if tools are available
        for key, Tool_class in tools.items():
            try:
                tool = Tool_class()
                logging.info(f"{tool.name}: OK (version: {tool.version})")
            except BaseException:
                raise RuntimeError(f'Dependency not found: {key}')

    @staticmethod
    def parse_arguments(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
        """
        Parses the command line arguments.
        :return: Parsed arguments
        """
        argument_parser = argparse.ArgumentParser()
        argument_parser.add_argument('--fasta', type=Path, required=True, help='Input FASTA file.')
        argument_parser.add_argument('--fasta-name', help='Name of the input FASTA file (for Galaxy input).')
        argument_parser.add_argument('--identity-cutoff', default=80, type=int, help='Clustering identity cutoff, entries with a higher value are combined into a single cluster.')
        argument_parser.add_argument('--output-html', type=Path, help='Output HTML file with database construction information.')
        argument_parser.add_argument('--output-dir', type=Path, required=True, help='Output directory.')
        argument_parser.add_argument('--working-dir', default=Path.cwd(), type=Path, help='Working directory for temporary files.')
        argument_parser.add_argument('--threads', type=int, default=4, help='Number of threads to use.')
        return argument_parser.parse_args(args)

    def run(self) -> None:
        """
        Runs this tool.
        :return: None
        """
        self._check_dependencies()
        if not self._args.output_dir.exists():
            self._args.output_dir.mkdir(parents=True)
        input_fasta = self._helper.standardize_fasta_headers(self._args.fasta)
        self.__export_blast_db(input_fasta, self._args.output_dir)
        self.__export_srst2_db(input_fasta, self._args.output_dir)
        self._helper.export_metadata(self._db_name, self._args.output_dir)
        self.__export_report()

    def __export_blast_db(self, input_fasta: Path, output_dir: Path) -> None:
        """
        Creates and exports a gene detection BLAST database from the given FASTA file.
        :param input_fasta: Input FASTA file
        :param output_dir: Output directory
        :return: None
        """
        # Create file
        dir_indexing = self._helper.get_working_subdir('index_blast')
        new_path = dir_indexing / input_fasta.name
        shutil.copyfile(str(input_fasta), str(new_path))

        # Index
        self._helper.index_blast(new_path, dir_indexing)

        # Export files
        for f in dir_indexing.iterdir():
            shutil.copyfile(str(f), str(output_dir / f.name))

    def __export_srst2_db(self, input_fasta: Path, output_dir: Path) -> None:
        """
        Exports a database for SRST2.
        :param input_fasta: Input FASTA file
        :param output_dir: Output directory
        :return: None
        """
        # Cluster FASTA
        dir_clustering = self._helper.get_working_subdir('clustering')
        fasta_seq_headers = dir_clustering / 'seq_headers.fasta'
        self._new_name_by_header = self._helper.convert_fasta_headers_to_seq(input_fasta, fasta_seq_headers)
        self._clusters = self._helper.get_clusters_form_fasta(fasta_seq_headers, self._args.identity_cutoff)

        # Create SRST2 FASTA
        dir_indexing = self._helper.get_working_subdir('index_srst2')
        fasta_srst2 = dir_indexing / f'{self._db_name}-clustered_{self._args.identity_cutoff}.fasta'
        self._helper.create_srst2_fasta(fasta_seq_headers, fasta_srst2, self._clusters)

        # Index
        self._helper.index_blast(fasta_srst2, dir_indexing)

        # Export files
        self._helper.export_mapping(self._new_name_by_header, self._clusters, output_dir)
        for f in dir_indexing.iterdir():
            if f.is_file():
                shutil.copyfile(str(f), str(output_dir / f.name))
            elif f.is_dir():
                shutil.copytree(str(f), str(output_dir / f.name))

    def __export_report(self) -> None:
        """
        Creates a report with some info on the database.
        :return: None
        """
        if self._args.output_html is None:
            self._args.output_html = self._args.output_dir / 'report.html'
        self._report = HtmlReport(self._args.output_html, self._args.output_dir)
        path_css = Path(str(files('camel').joinpath('resources/style.css')))
        self._report.initialize('Gene detection database', path_css)
        self._report.add_html_object(self.__create_db_info_section())
        self._report.add_html_object(self.__create_clusters_section())
        self._report.add_html_object(SnakePipelineUtils.create_commands_section(
            self._helper.informs, self._args.working_dir))
        self._report.save()

    def __create_db_info_section(self) -> HtmlReportSection:
        """
        Creates the report section with the database info.
        :return: HTML report section
        """
        section_db_info = HtmlReportSection('Database info')
        section_db_info.add_table([
            ['Name:', self._db_name],
            ['Size:', sum(len(c.seq_ids) for c in self._clusters)],
            ['Nb. clusters:', len(self._clusters)],
            ['Clustering cutoff: ', f'{self._args.identity_cutoff}%']
        ], table_attributes=[('class', 'information')])
        return section_db_info

    def __create_clusters_section(self) -> HtmlReportSection:
        """
        Creates the report section with the cluster information.
        :return: HTML report section
        """
        section_clusters = HtmlReportSection('Clusters')
        allele_by_seq_id = {
            s: GeneDetectionUtils.parse_header(h)[1]['allele'] for s, h in self._new_name_by_header.items()}
        table_data = [[
            cluster.name,
            len(cluster.seq_ids),
            ', '.join([allele_by_seq_id[s] for s in cluster.seq_ids])
        ] for cluster in self._clusters]
        section_clusters.add_table(table_data, ['Cluster', 'Size', 'Sequence ids'], [('class', 'data')])
        return section_clusters


if __name__ == '__main__':
    loggingutils.initialize_logging()
    main = MainMakeGeneDetectionDB()
    main.run()
