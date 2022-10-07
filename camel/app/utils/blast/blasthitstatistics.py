from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

from camel.app.utils.blast.blastformat7parser import BlastFormat7Parser

BLASTN_OUTPUT_FORMAT = '"7 pident sseqid sseq slen qseqid qstart qend"'


@dataclass
class BlastHitStatistics:
    """
    This class contains the statistics for a BLAST hit.
    """
    subject_id: str
    subject_length: int
    subject_sequence: str
    query_id: str
    query_start: int
    query_end: int
    percent_identity: float

    @staticmethod
    def parse_blast_output(output_path: Path) -> List['BlastHitStatistics']:
        """
        Parses a BLAST output file generated with the output format defined above.
        :return: List of parsed BLAST statistics
        """
        return [BlastHitStatistics.create_from_dict(d) for d in BlastFormat7Parser.parse_output_file(output_path)]

    @staticmethod
    def create_from_dict(info: Dict[str, Any]) -> 'BlastHitStatistics':
        """
        Creates a BLAST hit statistic from a parsed BLAST output dictionary.
        :param info: Info dictionary
        :return: Blast hit statistics
        """
        try:
            return BlastHitStatistics(
                str(info['sseqid']),
                int(info['slen']),
                info['sseq'],
                str(info['qseqid']),
                int(info['qstart']),
                int(info['qend']),
                float(info['pident'])
            )
        except KeyError as err:
            raise ValueError(f"Key '{err}' missing from blast output")

    @property
    def alignment_length(self) -> int:
        """
        Returns the length of the alignment.
        :return: Length of the alignment
        """
        return len(self.subject_sequence)

    @property
    def subject_coverage(self) -> float:
        """
        Returns the fraction of the subject that is covered by the alignment.
        :return: % subject covered
        """
        return 100.0 * float(self.alignment_length) / self.subject_length

    def is_full_length(self) -> bool:
        """
        Function to check if this is a full length hit
        :return: True if full length hit
        """
        return self.subject_length == self.alignment_length

    def is_perfect_hit(self) -> bool:
        """
        Function to check if this is a perfect hit.
        :return: True if perfect, False otherwise
        """
        return self.is_full_length() and (self.percent_identity == 100.0)

    @property
    def gaps(self) -> int:
        """
        Returns the number of gaps in the alignment.
        :return: Number of gaps
        """
        return self.subject_sequence.count('-')

    @property
    def length_statistic(self) -> str:
        """
        Returns the length in the format: {bases_covered}/{subject_length}.
        :return: Length statistic
        """
        return f'{self.alignment_length}/{self.subject_length}'
