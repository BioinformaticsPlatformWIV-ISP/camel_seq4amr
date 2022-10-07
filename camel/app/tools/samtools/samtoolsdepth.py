from pathlib import Path
from typing import List, Union

from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.samtools.samtoolsbase import SamtoolsBase


class SamtoolsDepth(SamtoolsBase):

    """
    Calculates the coverage depth of an alignment.
    """

    def __init__(self) -> None:
        """
        Initializes this tool.
        """
        super().__init__('samtools depth', '1.9')

    def _check_input(self) -> None:
        """
        Checks the input.
        :return: None
        """
        if 'BAM' not in self._tool_inputs:
            if 'CRAM' not in self._tool_inputs:
                raise ValueError("No BAM or CRAM input file found")
        if len(self._tool_inputs['BAM']) != 1:
            raise ValueError("Exactly one BAM input file expected")
        super(SamtoolsBase, self)._check_input()

    def _execute_tool(self) -> None:
        """
        Executes this tool.
        :return: None
        """
        self.__build_command()
        self._execute_command()
        self.__set_output()

    def __build_command(self) -> None:
        """
        Builds the command.
        :return: None
        """
        parts = [self._tool_command]
        options = self._build_options(['output_filename'])
        if len(options) > 0:
            parts.extend(options)
        if 'BED' in self._tool_inputs:
            parts.append(f"-b {self._tool_inputs['BED'][0].path}")
        if 'BAM' in self._tool_inputs:
            parts.extend([str(self._tool_inputs['BAM'][0].path), f" > {self._parameters['output_filename'].value}"])
        elif 'CRAM' in self._tool_inputs:
            parts.extend([str(self._tool_inputs['CRAM'][0].path), f" > {self._parameters['output_filename'].value}"])
        self._command.command = ' '.join(parts)

    def __set_output(self) -> None:
        """
        Sets the output of this tool.
        :return: None
        """
        output_file_path = self.folder / self._parameters['output_filename'].value
        self._tool_outputs['TSV'] = [ToolIOFile(output_file_path)]
        self._informs['median_depth'] = SamtoolsDepth.calculate_median_coverage(output_file_path)

    @staticmethod
    def median(input_list: List[int]) -> Union[float, int]:
        """
        Returns the median value of a list.
        :return:
        """
        if len(input_list) == 0:
            return 0
        sorted_list = sorted(input_list)
        middle = len(input_list) // 2
        if len(input_list) % 2:
            return sorted_list[middle]
        else:
            median = (sorted_list[middle] + sorted_list[middle - 1]) / 2
            return median

    @staticmethod
    def calculate_median_coverage(output_path: Path) -> Union[float, int]:
        """
        Calculates the median coverage.
        :param output_path: Path to the output files.
        :return: None
        """
        coverage_values = []
        with output_path.open() as output_file:
            for line in output_file.readlines():
                seq_id, pos, count = line.split('\t')
                coverage_values.append(int(count))
        return SamtoolsDepth.median(coverage_values)
