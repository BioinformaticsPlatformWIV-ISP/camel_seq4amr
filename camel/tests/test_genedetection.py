import logging
import tempfile
import unittest
from pathlib import Path

import pkg_resources

from camel.app.loggingutils import initialize_logging
from camel.config import config
from camel.scripts.maingenedetection import MainGeneDetection


class TestGeneDetection(unittest.TestCase):
    """
    Tests the gene detection workflow.
    """
    FASTA_IN = Path(pkg_resources.resource_filename('camel', 'data/assembly_subset.fasta'))
    FASTA_IN_GALAXY = Path(pkg_resources.resource_filename('camel', 'data/dataset_000.dat'))
    FQ_ILMN_PE_IN = [
        Path(pkg_resources.resource_filename('camel', 'data/reads_illumina_1.fastq.gz')),
        Path(pkg_resources.resource_filename('camel', 'data/reads_illumina_2.fastq.gz'))
    ]
    FQ_ILMN_PE_IN_NO_HITS = [
        Path(pkg_resources.resource_filename('camel', 'data/reads_no_hit_1.fastq')),
        Path(pkg_resources.resource_filename('camel', 'data/reads_no_hit_2.fastq'))
    ]
    FQ_IONTORRENT_SE_IN = Path('/testdata/camel/gene_detection/iontorrent/reads_iontorrent.fastq')
    DB_IN = Path(pkg_resources.resource_filename('camel', 'data/db_amr'))

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

    ###############
    # FASTQ input #
    ###############
    # BLAST
    def test_gene_detection_blast_illumina(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on Illumina data.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-pe', str(TestGeneDetection.FQ_ILMN_PE_IN[0]), str(TestGeneDetection.FQ_ILMN_PE_IN[1]),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--assembly-kmers', '33,55'
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    def test_gene_detection_blast_illumina_fasta_out(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on Illumina data and saving of the assembly.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        path_fasta_out = self.running_dir / 'report' / 'assembly.fasta'
        args = [
            '--fastq-pe', str(TestGeneDetection.FQ_ILMN_PE_IN[0]), str(TestGeneDetection.FQ_ILMN_PE_IN[1]),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-fasta', str(path_fasta_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--assembly-kmers', '33,55'
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)
        self.assertGreater(path_fasta_out.stat().st_size, 0)

    def test_gene_detection_blast_illumina_trim(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on Illumina data, including trimming.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-pe', str(TestGeneDetection.FQ_ILMN_PE_IN[0]), str(TestGeneDetection.FQ_ILMN_PE_IN[1]),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--trim-reads',
            '--assembly-kmers', '33,55',
            '--adapter', 'TruSeq2'
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    def test_gene_detection_blast_iontorrent(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on IonTorrent data, including trimming.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-se', str(TestGeneDetection.FQ_IONTORRENT_SE_IN),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--read-type', 'iontorrent',
            '--assembly-kmers', '33,55'
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    def test_gene_detection_blast_iontorrent_trim(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on IonTorrent data, including trimming.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-se', str(TestGeneDetection.FQ_IONTORRENT_SE_IN),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--read-type', 'iontorrent',
            '--trim-reads',
            '--assembly-kmers', '33,55'
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    # KMA
    def test_gene_detection_kma_illumina(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on Illumina data, including trimming.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-pe', str(TestGeneDetection.FQ_ILMN_PE_IN[0]), str(TestGeneDetection.FQ_ILMN_PE_IN[1]),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--read-type', 'illumina',
            '--detection-method', 'kma',
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    def test_gene_detection_kma_illumina_trim(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on Illumina data, including trimming.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-pe', str(TestGeneDetection.FQ_ILMN_PE_IN[0]), str(TestGeneDetection.FQ_ILMN_PE_IN[1]),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--read-type', 'illumina',
            '--detection-method', 'kma',
            '--adapter', 'TruSeq3',
            '--trim-reads'
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    def test_gene_detection_kma_iontorrent(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on IonTorrent data, including trimming.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-se', str(TestGeneDetection.FQ_IONTORRENT_SE_IN),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--read-type', 'iontorrent',
            '--detection-method', 'kma',
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    def test_gene_detection_kma_iontorrent_trim(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on IonTorrent data, including trimming.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-se', str(TestGeneDetection.FQ_IONTORRENT_SE_IN),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--read-type', 'iontorrent',
            '--detection-method', 'kma',
            '--trim-reads'
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    # SRST2
    def test_gene_detection_srst2_illumina(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on Illumina data, including trimming.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-pe', str(TestGeneDetection.FQ_ILMN_PE_IN[0]), str(TestGeneDetection.FQ_ILMN_PE_IN[1]),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--read-type', 'illumina',
            '--detection-method', 'srst2'
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    def test_gene_detection_srst2_illumina_trim(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on Illumina data, including trimming.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-pe', str(TestGeneDetection.FQ_ILMN_PE_IN[0]), str(TestGeneDetection.FQ_ILMN_PE_IN[1]),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--read-type', 'illumina',
            '--detection-method', 'srst2',
            '--trim-reads'
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    def test_gene_detection_srst2_iontorrent(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on Illumina data, including trimming.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-se', str(TestGeneDetection.FQ_IONTORRENT_SE_IN),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--read-type', 'iontorrent',
            '--detection-method', 'srst2',
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    def test_gene_detection_srst2_iontorrent_trim(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on Illumina data, including trimming.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-se', str(TestGeneDetection.FQ_IONTORRENT_SE_IN),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--read-type', 'iontorrent',
            '--detection-method', 'srst2',
            '--trim-reads'
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    #################
    # Special cases #
    #################
    def test_gene_detection_srst2_illumina_read_names(self) -> None:
        """
        Tests the gene detection workflow with BLAST detection on Illumina data, including trimming.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-pe', str(TestGeneDetection.FQ_ILMN_PE_IN[0]), str(TestGeneDetection.FQ_ILMN_PE_IN[1]),
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--fastq-pe-names', 'MB3984_S29_L001_R1_001.fastq.gz', 'MB3984_S29_L001_R2_001.fastq.gz',
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--read-type', 'illumina',
            '--detection-method', 'srst2'
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    def test_gene_detection_blast_fasta_input_galaxy(self) -> None:
        """
        Tests the gene detection main script using blast with an input file in the Galaxy name style..
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

    def test_gene_detection_blast_fasta_input_spaces(self) -> None:
        """
        Tests the gene detection main script using blast.
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

    def test_gene_detection_srst2_no_hits(self) -> None:
        """
        Tests the gene detection main script using SRST2 where no hits are detected.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-pe', *[str(x) for x in TestGeneDetection.FQ_ILMN_PE_IN_NO_HITS],
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--detection-method', 'srst2',
            '--trim-reads'
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)

    def test_gene_detection_srst2_galaxy_trimmomatic(self) -> None:
        """
        Tests the gene detection main script using blast with output generated by trimmomatic in Galaxy.
        :return: None
        """
        path_report_out = self.running_dir / 'report' / 'report.html'
        args = [
            '--fastq-pe', str(TestGeneDetection.FQ_ILMN_PE_IN[0]), str(TestGeneDetection.FQ_ILMN_PE_IN[1]),
            '--fastq-pe-names',
            'Trimmomatic on Neisseria_2.fastq (R1 paired)', 'Trimmomatic on Neisseria_2.fastq (R2 paired)',
            '--database-dir', str(TestGeneDetection.DB_IN),
            '--output-html', str(path_report_out),
            '--output-dir', str(path_report_out.parent),
            '--working-dir', str(self.running_dir),
            '--detection-method', 'srst2',
        ]
        main = MainGeneDetection(args)
        main.run()
        self.assertGreater(path_report_out.stat().st_size, 0)


if __name__ == '__main__':
    initialize_logging()
    unittest.main()
