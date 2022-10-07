from pathlib import Path

from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.tool import Tool
from camel.app.utils.fastqutils import FastqUtils


class FastqQualityTrimmer(Tool):
    """
    Trims and filters reads based on the quality scores.
    """

    def __init__(self) -> None:
        """
        Initializes this tool.
        """
        super().__init__('Fastx: fastq quality trimmer', '0.0.13')

    def _execute_tool(self) -> None:
        """
        Executes this tool.
        :return: None
        """
        output_path = self.folder / self._parameters['output_filename'].value
        self.__build_command(output_path)
        self._execute_command()
        self._tool_outputs['FASTQ'] = [ToolIOFile(output_path)]
        self.__set_informs(output_path)

    def __build_command(self, output_path: Path) -> None:
        """
        Builds the command line call.
        :param output_path: Output path
        :return: None
        """
        self._command.command = ' '.join([
            self._tool_command,
            '-i {}'.format(self._tool_inputs['FASTQ'][0].path),
            '-o {}'.format(output_path),
            ' '.join(self._build_options(excluded_parameters=['output_filename']))
        ])

    def __set_informs(self, output_path: Path) -> None:
        """
        Sets the informs for this tool.
        :param output_path: Output path
        :return: None
        """
        input_reads = FastqUtils.count_reads(self._tool_inputs['FASTQ'][0].path)
        output_reads = FastqUtils.count_reads(output_path)
        self._informs['input_reads'] = input_reads
        self._informs['output_reads'] = output_reads
        self._informs['perc_surviving'] = 100.0 * output_reads / input_reads
