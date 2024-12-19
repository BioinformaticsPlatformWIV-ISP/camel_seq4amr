import logging
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path

from camel.app.loggingutils import initialize_logging
from camel.config import config
from camel.scripts.maingenedetection import MainGeneDetection


class TestGeneDetection(unittest.TestCase):
    """
    Tests the gene detection workflow.
    """
    FASTA_IN = Path(str(files('camel').joinpath('data/assembly_subset.fasta')))
    FASTA_IN_GALAXY = Path(str(files('camel').joinpath('data/dataset_000.dat')))
    DB_IN = Path(str(files('camel').joinpath('data/db_amr')))

    def setUp(self) -> None:
        """
        Sets up the resources before running the test.
        :return: None
        """
        self.running_dir = Path(tempfile.mkdtemp(None, 'camel_', config['dir_temp']))
        logging.debug(f"Directory for testing: {self.running_dir}")

    ###############
    # FASTA input #
    ###############
    def test_gene_detection_blast_fasta(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on FASTA input.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fasta', str(TestGeneDetection.FASTA_IN),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    def test_gene_detection_blast_fasta_galaxy(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on FASTA input in Galaxy format.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fasta', str(TestGeneDetection.FASTA_IN_GALAXY),
            '--fasta-name', TestGeneDetection.FASTA_IN.name,
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir)
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    def test_gene_detection_blast_fasta_spaces(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on FASTA input with spaces in the name.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fasta', str(TestGeneDetection.FASTA_IN_GALAXY),
            '--fasta-name', '"my reference genome.fasta"',
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir)
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)


if __name__ == '__main__':
    initialize_logging()
    unittest.main()
