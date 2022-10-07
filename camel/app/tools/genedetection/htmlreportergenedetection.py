import logging
from pathlib import Path
from typing import List, Dict

from camel.app.error.invalidinputspecificationerror import InvalidInputSpecificationError
from camel.app.io.tooliovalue import ToolIOValue
from camel.app.tools.tool import Tool
from camel.app.utils.fileutils import FileUtils
from camel.app.utils.genedetection.genedetectionhitbase import GeneDetectionHitBase
from camel.app.utils.report.htmlreportsection import HtmlReportSection


class HtmlReporterGeneDetection(Tool):
    """
    Tool that creates HTML reports for the gene detection pipeline.
    """

    def __init__(self) -> None:
        """
        Initialize this tool.
        :return: None
        """
        super().__init__('Gene Detection: Report', '0.1')
        self._sub_folder = None
        self._report_section = None

    def _execute_tool(self) -> None:
        """
        Executes this tool.
        :return: None
        """
        self.__initialize_report()
        self.__add_parameter_table(self._input_informs['detection'])
        if len(self._tool_inputs['VAL_Hits']) == 0:
            self._report_section.add_paragraph('No hits found.')
        else:
            self.__add_output_table([h.value for h in self._tool_inputs['VAL_Hits']])
        self.__add_database_information()

        # Add a warning when the detection method is different from the general detection
        if 'forced_detection_method' in self._parameters:
            self._report_section.add_alert(
                f"Detection for this DB is always done using '{self._parameters['forced_detection_method'].value}', "
                f"regardless of pipeline setting.", 'info')
        self._tool_outputs['VAL_HTML'] = [ToolIOValue(self._report_section)]

    def _check_input(self) -> None:
        """
        Checks if the input is valid.
        :return: None
        """
        if 'db_info' not in self._input_informs:
            raise InvalidInputSpecificationError("No database info found")
        if 'VAL_Hits' not in self._tool_inputs:
            logging.warning("No blast hits found")
        if ('VAL_Hits' in self._tool_inputs) and (len(self._tool_inputs['VAL_Hits']) > 0) and \
                ('TSV' not in self._tool_inputs):
            raise InvalidInputSpecificationError("TSV input is required when hits were detected.")
        super(HtmlReporterGeneDetection, self)._check_input()

    def __initialize_report(self) -> None:
        """
        Initializes the HTML report.
        :return: None
        """
        db_name = self._input_informs['db_info']['name']
        self._report_section = HtmlReportSection(self._input_informs['db_info']['title'], 3)
        self._sub_folder = Path('gene_detection') / FileUtils.make_valid(db_name)

    def __add_parameter_table(self, informs_detection: Dict[str, str]) -> None:
        """
        Adds a tables with the parameters used for the detection.
        :param informs_detection: Informs from the detection
        :return: None
        """
        self._report_section.add_table([
            [f'{key}:', value] for key, value in sorted(informs_detection.items()) if not key.startswith('_')
        ], None, [('class', 'information')])

    def __add_output_table(self, hits: List[GeneDetectionHitBase]) -> None:
        """
        Adds the output table.
        :param hits: Detected hits
        :return: None
        """
        table_data = [hit.to_html_row(self._report_section, self._sub_folder) for hit in sorted(
            hits, key=lambda x: x.locus)]
        self._report_section.add_table(table_data, hits[0].html_column_names, [('class', 'data')])
        relative_path = self._sub_folder / Path(self._tool_inputs['TSV'][0].path).name
        self._report_section.add_file(self._tool_inputs['TSV'][0].path, relative_path)
        self._report_section.add_link_to_file("Download (TSV)", relative_path)

    def __add_database_information(self) -> None:
        """
        Adds the database information to the report.
        :return: None
        """
        self._report_section.add_paragraph('Last updated: {}'.format(self._input_informs['db_info'].get(
            'last_updated', '{LAST_UPDATED}')))
