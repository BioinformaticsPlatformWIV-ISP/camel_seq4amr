
from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.blast.blast import Blast


class BlastFormatter(Blast):
    """
    Formats BLAST output.
    """

    def __init__(self) -> None:
        """
        Initializes this tool.
        """
        super().__init__('blast_formatter')

    def _check_input(self) -> None:
        """
        Checks whether the required input files are specified.
        :return: None
        """
        if 'ASN' not in self._tool_inputs:
            raise ValueError('No blast archive input found')
        super()._check_input()

    def _execute_tool(self) -> None:
        """
        Runs Blast.
        :return: None
        """
        self.__output_key = self.__get_output_key()
        self.__build_command()
        self._execute_command()
        self.__set_output()

    def __get_output_key(self) -> str:
        """
        Returns the output key.
        :return: Output key
        """
        if 'create_html_output' in self._parameters:
            return 'HTML'
        output_format = self._parameters['output_format'].value
        if output_format == '5':
            return 'XML'
        elif '6' in output_format or '7' in output_format:
            return 'TSV'
        elif output_format in ('8', '9', '11'):
            return 'ASN'
        elif '10' in output_format:
            return 'CSV'
        elif output_format == '12':
            return 'JSON'
        else:
            return 'TXT'

    def __build_command(self) -> None:
        """
        Builds the command line string.
        :return: None
        """
        blast_archive = self._tool_inputs['ASN'][0].path
        output_name = self.__get_output_name()
        options = ' '.join(self._build_options())
        self._command.command = f'{self._tool_command} -archive {blast_archive} -out {output_name} {options}'

    def __get_output_name(self) -> str:
        """
        Generates the default output name.
        :return: Output name
        """
        base_filename = self._tool_inputs['ASN'][0].path.stem
        return f'{base_filename}_formatted.{self.__output_key.lower()}'

    def __set_output(self) -> None:
        """
        Sets the output of this tool.
        :return: None
        """
        self._tool_outputs[self.__output_key] = [ToolIOFile(self.folder / self.__get_output_name())]

    def _check_command_output(self):
        """
        Checks the command output for errors.
        :return: None
        """
        if 'error' in self.stderr.lower() or self._command.returncode != 0:
            raise ToolExecutionError("Error executing {}: {}".format(self.name, self._command.stderr.strip()))
