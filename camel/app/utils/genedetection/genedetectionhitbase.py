from pathlib import Path
from typing import List, Optional, Union, Any

import abc

from camel.app.utils.genedetection.genedetectionutils import GeneDetectionUtils
from camel.app.utils.report.htmlreportsection import HtmlReportSection
from camel.app.utils.report.htmltablecell import HtmlTableCell


class GeneDetectionHitBase(object, metaclass=abc.ABCMeta):
    """
    This is the base class for hits detected by the gene detection workflows.
    """

    def __init__(self, locus: str, accession: Optional[str] = None) -> None:
        """
        Initializes the hit.
        :param locus: Locus corresponding to the hit.
        :param accession: Accession number
        """
        self._locus = locus
        self._accession = accession
        self._metadata = []

    @property
    def locus(self) -> str:
        """
        Returns the locus.
        :return: Locus name
        """
        return self._locus

    @locus.setter
    def locus(self, locus: str) -> None:
        """
        Sets the locus for this hit.
        :param locus: Locus
        :return: None
        """
        self._locus = locus

    @property
    def accession(self) -> Optional[str]:
        """
        Returns the accession.
        :return: Accession
        """
        return self._accession

    @accession.setter
    def accession(self, accession: str) -> None:
        """
        Setter for the accession.
        :param accession: Accession number
        :return: None
        """
        self._accession = accession

    @abc.abstractmethod
    def is_perfect_hit(self) -> bool:
        """
        Function to check if this is a perfect hit.
        :return: True if perfect hit, False otherwise
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def is_full_length(self) -> bool:
        """
        Function to check if this is a full length hit.
        :return: True if full length, False otherwise
        """
        raise NotImplementedError()

    @property
    def color(self) -> str:
        """
        Returns the color for this hit.
        Green: Perfect hit
        Light green: Full length hit with one or more mismatches
        Grey: Non-full length hit
        :return: Color
        """
        if self.is_perfect_hit():
            return 'green'
        elif self.is_full_length():
            return 'lightgreen'
        else:
            return 'grey'

    @property
    @abc.abstractmethod
    def table_column_names(self) -> List[str]:
        """
        Returns the names of the columns of the tabular output.
        :return: List of column names
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def to_table_row(self) -> List[str]:
        """
        Returns the hit as a table row.
        :return: List of table cell values
        """
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def html_column_names(self) -> List[str]:
        """
        Returns the names of the columns of the HTML output.
        :return: List of column names
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def to_html_row(self, report_section: HtmlReportSection, sub_directory: Path, colored: bool = True) \
            -> List[Union[str, HtmlTableCell]]:
        """
        Returns the hit as a HTML table row.
        :param report_section: Section is passed to save additional data
        :param sub_directory: Subdirectory to save the additional data
        :param colored: If True, the row is colored
        :return: List of table cell values
        """
        raise NotImplementedError()

    def add_metadata(self, name: str, value: str) -> None:
        """
        Adds metadata to the hit.
        :param name: Metadata title
        :param value: Metadata value
        :return: None
        """
        self._metadata.append({'name': name, 'value': value})

    def _get_accession_cell(self) -> HtmlTableCell:
        """
        Returns the table cell for the accession.
        :return: Table cell with accession
        """
        if self._accession is None:
            return HtmlTableCell('-', self.color)
        elif GeneDetectionUtils.is_ncbi_accession(self._accession):
            link = f'https://www.ncbi.nlm.nih.gov/nuccore/{self._accession}'
            return HtmlTableCell(self._accession, self.color, link=link)
        else:
            return HtmlTableCell(self._accession, self.color)

    def get_metadata_value(self, key) -> Any:
        """
        Returns the value for the metadata with the given key.
        :param key: Key
        :return: Value
        """
        for dict_ in self._metadata:
            if dict_['name'] == key:
                return dict_['value']
        raise KeyError(key)
