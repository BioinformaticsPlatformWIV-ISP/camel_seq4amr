import gzip
import logging
import re
from pathlib import Path
from typing import Set, Union, List, Optional, Tuple

from Bio import SeqIO

from camel.app.utils.command import Command
from camel.app.utils.fileutils import FileUtils


class FastqUtils(object):

    """
    This class contains utility function to work with FASTQ files.
    """

    PATTERN_FQ_PE = r'(.+?)(_S\d+)?(_L\d{3})?[_.]R?1P?(_\d+)?.(fastq|fq)(.gz)?'
    PATTERN_FQ_SE = r'(.+?)(_S\d+)?(_L\d{3})?(_\d+)?.(fastq|fq)(.gz)?'

    @staticmethod
    def count_reads(infile: Path) -> int:
        """
        Count how many reads in a fastq file
        :param infile: file name of the fastq file to count
        :return: number of reads in fastq file
        """
        cat = 'zcat' if FileUtils.is_gzipped(infile) else 'cat'
        command = Command(f"{cat} {infile} | paste - - - - | wc -l")
        command.run(infile.resolve().parent)
        if command.stderr != '':
            raise RuntimeError(command.stderr, command.command)
        return int(command.stdout.rstrip())

    @staticmethod
    def get_sample_name(fastq_path: Union[Path, str], pattern: str = PATTERN_FQ_PE) -> str:
        """
        Returns the sample name based on the given reads.
        :param fastq_path: FASTQ path
        :param pattern: Regex to determine the sample name
        :return: Sample name
        """
        basename = FileUtils.make_valid(Path(fastq_path).name)
        m = re.match(pattern, basename, re.IGNORECASE)
        if m:
            return m.group(1)
        raise ValueError(f"Cannot determine sample name from: {basename}")

    @staticmethod
    def get_all_read_names(fastq_path: Path) -> Set[str]:
        """
        Retrieves all read names from the given fastq file
        :param fastq_path: Path to the fastq file
        :return: Set with read names
        """
        read_names = set()
        open_fn = gzip.open if FileUtils.is_gzipped(fastq_path) else open
        with open_fn(fastq_path, 'rt') as handle:
            for record in SeqIO.parse(handle, 'fastq'):
                read_names.add(record.id)
        return read_names

    @staticmethod
    def count_bases(input_file: Path) -> int:
        """
        Calculates the number of bases in the given input files
        :param input_file: File path
        :return: Number of bases
        """
        cat = 'zcat' if FileUtils.is_gzipped(input_file) else 'cat'
        cmd = f"{cat} {input_file} | paste - - - - | cut -f 2 | tr -d '\n' | wc -c"
        command = Command()
        command.command = cmd
        command.run(Path.cwd())
        return int(command.stdout)

    @staticmethod
    def determine_sample_name_from_fq(fastq_names: List[Path], is_pe: bool = True, default: Optional[str] = None) -> \
            str:
        """
        Determines the sample name from the given command line arguments.
        :param fastq_names: PE FASTQ PE file names
        :param is_pe: If true, FASTQ files are paired-end
        :param default: Default value when the name cannot be parsed
        :return: Sample name
        """
        logging.debug(f"Determining sample name from: {', '.join([p.name for p in fastq_names])}")
        pattern = FastqUtils.PATTERN_FQ_PE if is_pe else FastqUtils.PATTERN_FQ_SE
        try:
            return FastqUtils.get_sample_name(fastq_names[0], pattern)
        except ValueError:
            logging.debug("Filename does not match any standard FASTQ format")

        # Trimmomatic output files
        m = re.search(r'.+ on {}'.format(pattern), fastq_names[0].name)
        if m:
            return m.group(1)

        # Raise error when default could not be set
        if default is None:
            raise ValueError(f"Sample name cannot be determined from: {', '.join([p.name for p in fastq_names])}")
        return default

    @staticmethod
    def determine_read_status(path_fq: Path) -> Tuple[str, str]:
        """
        Attempts to determine the forward / reverse state designator of the reads based on the filename.
        This is useful for SRST2 which can have problems with uncommon read names.
        Supported formats: read_1P.fastq, read_1.fastq
        :param path_fq: Path to input FASTQ file
        :return: Forward designator, reverse designator
        """
        if re.match('.*(_[12]P\\.).*', path_fq.name) is not None:
            return '1P', '2P'
        elif re.match('.*(_[12]\\.).*', path_fq.name) is not None:
            return '_1', '_2'
        raise ValueError(f"Cannot determine read name from: {path_fq}")
