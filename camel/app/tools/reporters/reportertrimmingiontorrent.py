from pathlib import Path

from camel.app.io.tooliovalue import ToolIOValue
from camel.app.tools.tool import Tool
from camel.app.utils.report.htmlreportsection import HtmlReportSection


class ReporterTrimmingIonTorrent(Tool):
    """
    This class is used to create the trimming report for IonTorrent reads.
    """

    def __init__(self) -> None:
        """
        Initializes this tool.
        """
        super().__init__('Trimming-IonTorrent: reporter', '0.1')
        self._sub_folder = Path('read_trimming')
        self._report_section = None

    def _execute_tool(self) -> None:
        """
        Executes this tool.
        :return: None
        """
        self._report_section = HtmlReportSection('Read trimming', subtitle=self._input_informs['filt_len']['_name'])
        self.__add_fastqc_report('Pre-filtering', 'pre', 'HTML_PRE')
        self.__add_filtering_section()
        self.__add_fastqc_report('Post-filtering', 'post', 'HTML_POST')
        self._tool_outputs['VAL_HTML'] = [ToolIOValue(self._report_section)]

    def __add_fastqc_report(self, section_title: str, suffix: str, key: str) -> None:
        """
        Adds the given FastQC report to the report.
        :param section_title: Title for the section
        :param suffix: Suffix for storing trimmed reads file
        :param key: Tool input key
        :return: None
        """
        self._report_section.add_header(section_title, 3)
        relative_path = self._sub_folder / f'fastqc_report-{suffix}.html'
        self._report_section.add_file(self._tool_inputs[key][0].path, relative_path)
        self._report_section.add_link_to_file('FastQC report', relative_path)

    def __add_filtering_section(self) -> None:
        """
        Adds the filtering section.
        :return: None
        """
        self._report_section.add_header('Filtering', 3)
        header = ['Filter', 'Reads in', 'Reads out', 'Description']
        table_data = [
            ['Length >50', '{:,}'.format(self._input_informs['filt_len']['input_reads']), '{:,} ({:.2f}%)'.format(
                self._input_informs['filt_len']['output_reads'], self._input_informs['filt_len']['perc_surviving']),
             'Removes reads that are shorter than 50 bp'],
            ['Quality filter', '{:,}'.format(self._input_informs['filt_qual']['input_reads']), '{:,} ({:.2f}%)'.format(
                self._input_informs['filt_qual']['output_reads'], self._input_informs['filt_qual']['perc_surviving']),
             'Removes reads for which 20% of the bases had a Phred quality score <Q20.']
        ]
        self._report_section.add_table(table_data, header, [('class', 'data')])
