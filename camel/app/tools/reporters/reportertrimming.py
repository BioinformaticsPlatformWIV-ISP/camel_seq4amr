from pathlib import Path

from camel.app.error.invalidinputspecificationerror import InvalidInputSpecificationError
from camel.app.io.tooliovalue import ToolIOValue
from camel.app.tools.tool import Tool
from camel.app.utils.report.htmlreportsection import HtmlReportSection


class ReporterTrimming(Tool):
    """
    Tool to create HTML reports for the read trimming.
    """

    def __init__(self) -> None:
        """
        Initialize this tool.
        :return: None
        """
        super().__init__('Trimming: reporter', '0.1')
        self.__sub_folder = Path('read_trimming')
        self._report_section = None

    def _execute_tool(self) -> None:
        """
        Executes this tool.
        :return: None
        """
        self._report_section = HtmlReportSection('Read trimming', subtitle=self._input_informs['trimming']['_name'])
        self.__add_fastqc_reports('Pre-trimming', 'pre_trimming', 'HTML_PRE')
        self.__add_trimming_section_pe()
        if (self._parameters.get('export_fastq') is not None) and (
                self._parameters['export_fastq'].as_boolean() is True):
            self.__add_trimmed_read_files()
        else:
            self._report_section.add_text("Trimmed FASTQ files not exported, change pipeline options to include them.")
        self.__add_fastqc_reports('Post-trimming', 'post_trimming', 'HTML_POST')
        self._tool_outputs['VAL_HTML'] = [ToolIOValue(self._report_section, False)]

    def _check_input(self) -> None:
        """
        Checks if the input is valid.
        :return: None
        """
        if 'HTML_PRE' not in self._tool_inputs:
            raise InvalidInputSpecificationError("No pre-trimming reports found")
        if 'FASTQ_PE' not in self._tool_inputs and 'FASTQ_SE' not in self._tool_inputs:
            raise InvalidInputSpecificationError("No reads input found ('FASTQ_PE' or 'FASTQ_SE')")
        if 'HTML_POST' not in self._tool_inputs:
            raise InvalidInputSpecificationError("No post-trimming reports found")
        if 'trimming' not in self._input_informs:
            raise InvalidInputSpecificationError("No trimming info found")
        super()._check_input()

    def __add_fastqc_reports(self, header: str, dir_name: str, key: str) -> None:
        """
        Adds FastQC reports to the report. This function supports PE and SE input.
        :param header: Section header
        :param dir_name: Name of the directory to store files
        :param key: Input file key
        :return: None
        """
        self._report_section.add_header(header, 3)
        if len(self._tool_inputs[key]) == 1:
            relative_path = self.__sub_folder / dir_name / 'fastqc_report.html'
            self._report_section.add_file(self._tool_inputs[key][0].path, relative_path)
            self._report_section.add_link_to_file('FastQC report', relative_path)
        else:
            for fastqc_report, orientation in zip(self._tool_inputs[key], ('forward', 'reverse')):
                relative_path = self.__sub_folder / dir_name / f'fastqc_report_{orientation}.html'
                self._report_section.add_file(fastqc_report.path, relative_path)
                self._report_section.add_link_to_file(f'FastQC report ({orientation})', relative_path)

    def __add_trimming_section_pe(self) -> None:
        """
        Adds the read trimming section for PE reads.
        :return: None
        """
        self._report_section.add_header('Read trimming', 3)
        table_data = [
            ['Input reads pairs:', ReporterTrimming.__reformat_inform(
                self._input_informs['trimming']['paired_reads_in'])],
            ['Both surviving:', ReporterTrimming.__reformat_inform(
                self._input_informs['trimming']['paired_reads_out'])],
            ['Forward only surviving:', ReporterTrimming.__reformat_inform(
                self._input_informs['trimming']['forward_only_reads'])],
            ['Reverse only surviving:', ReporterTrimming.__reformat_inform(
                self._input_informs['trimming']['reverse_only_reads'])],
            ['Dropped:', ReporterTrimming.__reformat_inform(
                self._input_informs['trimming']['reads_drop'])]
        ]
        self._report_section.add_table(table_data, table_attributes=[('class', 'information')])

    @staticmethod
    def __reformat_inform(input_str: str) -> str:
        """
        This function is used to reformat an inform value to a more readable format.
        This function also works when the percentage is omitted.
        E.g. 5241241 (10.02%) -> 5.241.241 (10.02%)
        :param input_str: Input string
        :return: Reformatted inform
        """
        parts = input_str.split(' ')
        if len(parts) == 1:
            return '{:,}'.format(int(parts[0]))
        elif len(parts) == 2:
            return '{:,} {}'.format(int(parts[0]), parts[1])
        raise ValueError("Cannot parse: {}".format(input_str))

    def __add_trimmed_read_files(self) -> None:
        """
        Saves the PE trimmed reads in the output directory and adds them to the report.
        :return: None
        """
        for trimmed_reads_paired, orientation in zip(self._tool_inputs['FASTQ_PE'], ('forward', 'reverse')):
            filename = f'trimmed_reads_paired_{orientation}.fastq'
            relative_path = self.__sub_folder / 'read_trimming' / filename
            self._report_section.add_file(trimmed_reads_paired.path, relative_path)
            self._report_section.add_link_to_file(f'Trimmed reads paired ({orientation})', relative_path)
        self._report_section.add_line_break()

        if 'FASTQ_SE_FORWARD' in self._tool_inputs and len(self._tool_inputs['FASTQ_SE_FORWARD']) > 0:
            relative_path = self.__sub_folder / 'read_trimming' / 'trimmed_reads_unpaired_forward.fastq'
            self._report_section.add_file(self._tool_inputs['FASTQ_SE_FORWARD'][0].path, relative_path)
            self._report_section.add_link_to_file('Trimmed reads unpaired (forward)', relative_path)
        else:
            self._report_section.add_link_to_file('Trimmed reads unpaired (forward)', None)

        if 'FASTQ_SE_REVERSE' in self._tool_inputs and len(self._tool_inputs['FASTQ_SE_REVERSE']) > 0:
            relative_path = self.__sub_folder / 'read_trimming' / 'trimmed_reads_unpaired_reverse.fastq'
            self._report_section.add_file(self._tool_inputs['FASTQ_SE_REVERSE'][0].path, relative_path)
            self._report_section.add_link_to_file('Trimmed reads unpaired (reverse)', relative_path)
        else:
            self._report_section.add_link_to_file('Trimmed reads unpaired (reverse)', None)
