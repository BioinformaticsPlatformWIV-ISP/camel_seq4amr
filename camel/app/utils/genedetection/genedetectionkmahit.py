from typing import List, Optional, Union

from camel.app.utils.genedetection.genedetectionhitbase import GeneDetectionHitBase
from camel.app.utils.report.htmlreportsection import HtmlReportSection
from camel.app.utils.report.htmltablecell import HtmlTableCell


class GeneDetectionKMAHit(GeneDetectionHitBase):
    """
    Gene detection hit detected by KMA.
    """

    def __init__(self, cluster: str, locus: str, accession: Optional[str], subject: str, score: int, length: int,
                 p_ident: float, p_cov: float, depth: float) -> None:
        """
        Initializes the hit.
        :param cluster: Cluster
        :param locus: Locus
        :param accession: Accession
        :param subject: Original sequence subject
        :param score: Score
        :param length: (Subject) length
        :param p_ident: (Subject) percent identity
        :param p_cov: (Subject) percent coverage
        :param depth: mean read depth across sequence
        """
        super().__init__(locus, accession)
        self._cluster = cluster
        self._subject = subject
        self._score = score
        self._length = length
        self._p_ident = p_ident
        self._p_cov = p_cov
        self._depth = depth

    def is_perfect_hit(self) -> bool:
        """
        Function to check if this is a perfect hit.
        :return: True if perfect hit, False otherwise
        """
        return (self.percent_identity == 100.0) and (self.subject_coverage == 100.0)

    def is_full_length(self) -> bool:
        """
        Function to check if this is a full length hit.
        :return: True if full length, False otherwise
        """
        return self.subject_coverage == 100.0

    @property
    def table_column_names(self) -> List[str]:
        """
        Returns the names of the columns of the tabular output.
        :return: List of column names
        """
        columns = ['DB_cluster', 'Locus', 'Length', '% Identity', '% Covered', 'Depth', 'Accession']
        for metadata in self._metadata:
            columns.insert(-1, metadata['name'])
        return columns

    def to_table_row(self) -> List[str]:
        """
        Returns the hit as a table row.
        :return: List of table cell values
        """
        data = [
            self._cluster,
            self.locus,
            str(self._length),
            '{:.2f}'.format(self.percent_identity),
            '{:.2f}'.format(self.subject_coverage),
            '{:.2f}'.format(self._depth),
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
        return self.table_column_names[1:]

    def to_html_row(self, report_section: HtmlReportSection, sub_directory: str, colored: bool = True) -> List[
            Union[str, HtmlTableCell]]:
        """
        Returns the hit as a HTML table row.
        :param report_section: Section is passed to save additional data
        :param sub_directory: Subdirectory to save the additional data
        :param colored: If True, the row is colored
        :return: List of table cell values
        """
        return [HtmlTableCell(v, self.color) for v in self.to_table_row()][1:-1] + [self._get_accession_cell()]

    @property
    def subject(self) -> str:
        """
        Returns the subject (locus + allele id).
        :return: Subject
        """
        return self._subject

    @property
    def score(self) -> int:
        """
        Returns the K-mer score.
        :return: Score
        """
        return self._score

    @property
    def percent_identity(self) -> float:
        """
        Returns the percent identity.
        :return: Percent identity
        """
        return self._p_ident

    @property
    def subject_coverage(self) -> float:
        """
        Returns the fraction of the subject that is covered by the alignment.
        :return: % subject covered
        """
        return self._p_cov
