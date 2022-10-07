from pathlib import Path
from typing import Optional, List, Union

from camel.app.utils.blast.blasthitstatistics import BlastHitStatistics
from camel.app.utils.genedetection.genedetectionhitbase import GeneDetectionHitBase
from camel.app.utils.report.htmlreportsection import HtmlReportSection
from camel.app.utils.report.htmltablecell import HtmlTableCell


class GeneDetectionBlastHit(GeneDetectionHitBase):
    """
    This class represents a gene detection hit detected with BLAST.
    """

    def __init__(self, locus: str, accession: Optional[str], blast_stats: BlastHitStatistics) -> None:
        """
        Initializes this hit.
        :param locus: Locus
        :param accession: Accession
        :param blast_stats: BLAST hit statistics
        """
        super().__init__(locus, accession)
        self._blast_stats = blast_stats
        self._alignment_path = None

    def is_perfect_hit(self) -> bool:
        """
        Returns True if this is a perfect hit, False otherwise
        :return: None
        """
        return self._blast_stats.is_perfect_hit()

    def is_full_length(self) -> bool:
        """
        Returns True if this is a full length hit, False otherwise.
        :return: True if full length
        """
        return self._blast_stats.is_full_length()

    @property
    def table_column_names(self) -> List[str]:
        """
        Returns the names of the columns of the tabular output.
        :return: List of column names
        """
        columns = ['DB_cluster', 'Locus', '% Identity', 'HSP/Locus length', 'Contig', 'Position in contig', 'Accession']
        for metadata in self._metadata:
            columns.insert(-1, metadata['name'])
        return columns

    def to_table_row(self) -> List[str]:
        """
        Returns the hit as a table row.
        :return: List of table cell values
        """
        data = [
            self._blast_stats.subject_id.split('__')[1],
            self.locus,
            '{:.2f}'.format(self.blast_stats.percent_identity),
            f'{self.blast_stats.length_statistic}',
            self.blast_stats.query_id,
            f'{self.blast_stats.query_start}..{self.blast_stats.query_end}',
            self._accession if self._accession is not None else '-'
        ]
        for metadata in self._metadata:
            data.insert(-1, metadata['value'])
        return data

    @property
    def html_column_names(self) -> List[str]:
        """
        Returns the names of the columns of the HTML output.
        :return: List of column names
        """
        return self.table_column_names[1:] + ['Alignment']

    def to_html_row(self, report_section: HtmlReportSection, sub_directory: Path, colored: bool = True) -> List[
            Union[str, HtmlTableCell]]:
        """
        Returns the hit as a HTML table row.
        :param report_section: Section is passed to save additional data
        :param sub_directory: Subdirectory to save the additional data
        :param colored: If True, the row is colored
        :return: List of table cell values
        """
        if self.alignment_path is None:
            alignment_cell = '-'
        else:
            relative_path = sub_directory / 'alignments' / self.alignment_path.name
            report_section.add_file(self.alignment_path, relative_path)
            alignment_cell = HtmlTableCell('view', self.color if colored else None, link=str(relative_path))

        return [HtmlTableCell(v, self.color) for v in self.to_table_row()][1:-1] + [self._get_accession_cell()] + \
               [alignment_cell]

    @property
    def blast_stats(self) -> BlastHitStatistics:
        """
        Returns the BLAST stats for this hit.
        :return: BLAST stats
        """
        return self._blast_stats

    @property
    def alignment_path(self) -> Path:
        """
        Returns the path to the alignment file.
        :return: Alignment file
        """
        return self._alignment_path

    @alignment_path.setter
    def alignment_path(self, alignment_path: Path) -> None:
        """
        Sets the alignment path.
        :param alignment_path: Alignment path
        :return: None
        """
        self._alignment_path = alignment_path
