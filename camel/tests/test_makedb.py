import logging
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path

from camel.app.loggingutils import initialize_logging
from camel.config import config
from camel.scripts.mainmakegenedetectiondb import MainMakeGeneDetectionDB


class TestMakeDB(unittest.TestCase):
    """
    Tests the gene detection create DB tool.
    """

    FASTA_IN = Path(str(files('camel').joinpath('data/db_amr/amr_subset.fasta')))

    def setUp(self) -> None:
        """
        Sets up the resources before running the test.
        :return: None
        """
        self.running_dir = Path(tempfile.mkdtemp(None, 'camel_', config['dir_temp']))
        logging.debug(f"Directory for testing: {self.running_dir}")

    def test_gene_detection_create_db(self) -> None:
        """
        Tests the gene detection create db main script.
        :return: None
        """
        output_file_report = self.running_dir / 'report' / 'report.html'
        args = [
            '--output-html', str(output_file_report),
            '--output-dir', str(output_file_report.parent),
            '--fasta', str(TestMakeDB.FASTA_IN),
            '--working-dir', str(self.running_dir)
        ]
        main = MainMakeGeneDetectionDB(args)
        main.run()
        self.assertGreater(output_file_report.stat().st_size, 0)

    def test_gene_detection_create_db_spaces_in_name(self) -> None:
        """
        Tests the gene detection create db main script.
        :return: None
        """
        output_file_report = self.running_dir / 'report' / 'report.html'
        args = [
            '--output-html', str(output_file_report),
            '--output-dir', str(output_file_report.parent),
            '--fasta', str(TestMakeDB.FASTA_IN),
            '--fasta-name', '"spaces in name.fasta"',
            '--working-dir', str(self.running_dir),
            '--threads', '4'
        ]
        main = MainMakeGeneDetectionDB(args)
        main.run()
        self.assertGreater(output_file_report.stat().st_size, 0)


if __name__ == '__main__':
    initialize_logging()
    unittest.main()
