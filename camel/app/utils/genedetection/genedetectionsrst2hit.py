from typing import List, Union, Optional

from camel.app.utils.genedetection.genedetectionhitbase import GeneDetectionHitBase
from camel.app.utils.report.htmlreportsection import HtmlReportSection
from camel.app.utils.report.htmltablecell import HtmlTableCell


class GeneDetectionSRST2Hit(GeneDetectionHitBase):
    """
    This class represents a gene detection hit detected with BLAST.
    """

    def __init__(self, cluster: str, locus: str, accession: Optional[str], length: int, mismatches: str,
                 uncertainty: str, coverage: float, divergence: float, depth: float) -> None:
        """
        Initializes this hit.
        :param locus: Locus
        :param accession: Accession number
        """
        super().__init__(locus, accession)
        self.cluster = cluster
        self._length = length
        self._mismatches = mismatches
        self._coverage = coverage
        self._divergence = divergence
        self._uncertainty = uncertainty
        self._depth = depth

    def is_perfect_hit(self) -> bool:
        """
        Function to check if this is a perfect hit.
        :return: True if perfect hit, False otherwise
        """
        return self._mismatches == '' and self.is_full_length()

    def is_full_length(self) -> bool:
        """
        Function to check if this is a full length hit.
        :return: True if full length, False otherwise
        """
        return self._coverage == 100.0

    @property
    def table_column_names(self) -> List[str]:
        """
        Returns the names of the columns of the tabular output.
        :return: List of column names
        """
        columns = ['DB_cluster', 'Locus', 'Length', '% Covered', 'Mismatches', 'Uncertainty', 'Divergence (%)', 'Depth',
                   'Accession']
        for metadata in self._metadata:
            columns.insert(-1, metadata['name'])
        return columns

    def to_table_row(self) -> List[str]:
        """
        Returns the hit as a table row.
        :return: List of table cell values
        """
        data = [
            self.cluster,
            self.locus,
            str(self._length),
            '{:.2f}'.format(self._coverage),
            self._mismatches if self._mismatches != '' else '-',
            self._uncertainty if self._uncertainty != '' else '-',
            '{:.2f}'.format(self._divergence),
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

    def to_html_row(self, report_section: HtmlReportSection, sub_directory: str, colored: bool = True) \
            -> List[Union[str, HtmlTableCell]]:
        """
        Returns the hit as a HTML table row.
        :param report_section: Section is passed to save additional data
        :param sub_directory: Subdirectory to save the additional data
        :param colored: If True, the row is colored
        :return: List of table cell values
        """
        data = [
            self.locus,
            str(self._length),
            '{:.2f}'.format(self._coverage),
            self._mismatches if self._mismatches != '' else '-',
            self._uncertainty if self._uncertainty != '' else '-',
            '{:.2f}'.format(self._divergence),
            '{:.2f}'.format(self._depth)
        ]
        for metadata in self._metadata:
            data.append(metadata['value'])
        return [HtmlTableCell(value, self.color) for value in data] + [self._get_accession_cell()]
