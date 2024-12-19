import re
from pathlib import Path

from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.tool import Tool
from camel.app.utils.command import Command


class Blast(Tool):
    """
    Base class for BLAST tools.

    INPUT:
    - Query (FASTA): FASTA file
    - Subject (FASTA_Subject / DB_BLAST): Either a FASTA file or a BLAST database with the subject sequences
    """

    def __init__(self, tool_name: str) -> None:
        """
        Initializes this tool.
        :param tool_name: Tool name
        """
        super().__init__(tool_name)
        self.__subject_key = None

    def _execute_tool(self) -> None:
        """
        Runs Blast.
        :return: None
        """
        self.__subject_key = self.__get_subject_key()
        self.__output_key = self.__get_output_key()
        self.__build_command()
        self._execute_command()
        self.__set_output()

    def __get_subject_key(self) -> str:
        """
        Returns the key of the subject, this can be:
        - FASTA_Subject: FASTA file of the subject sequence
        - DB_BLAST: BLAST database created using makeblastdb.
        :return: Key
        """
        if all(key in self._tool_inputs for key in ['DB_BLAST', 'FASTA_Subject']):
            raise ValueError("Cannot use DB_BLAST and FASTA_Subject at the same time")
        elif 'DB_BLAST' in self._tool_inputs:
            return 'DB_BLAST'
        elif 'FASTA_Subject' in self._tool_inputs:
            return 'FASTA_Subject'
        else:
            raise ValueError("No subject (FASTA_Subject / DB_BLAST) found")

    def __get_output_key(self) -> str:
        """
        Returns the output key based on the output format.
        :return: Key
        """
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
        self._command.command = ' '.join([
            self._tool_command,
            f"-query {self._tool_inputs['FASTA'][0].path}",
            self.__get_subject_argument(),
            f'-out {self.__get_output_filename()}',
            ' '.join(self._build_options(excluded_parameters=['output_filename']))
        ])

    def __get_subject_argument(self) -> str:
        """
        Returns the command line argument for the subject.
        :return: Command line argument
        """
        if self.__subject_key == 'FASTA_Subject':
            return f"-subject {self._tool_inputs['FASTA_Subject'][0].path}"
        elif self.__subject_key == 'DB_BLAST':
            return f"-db {self._tool_inputs['DB_BLAST'][0].path}"

    def __get_output_filename(self) -> str:
        """
        Returns the name of the output file.
        :return: Output name
        """
        if 'output_filename' in self._parameters:
            return self._parameters['output_filename'].value
        else:
            return self.__get_default_output_name()

    def __get_default_output_name(self) -> str:
        """
        Generates the default output name.
        :return: Output name
        """
        fasta_file_basename = self._tool_inputs['FASTA'][0].path.stem
        return f'{self._tool_command}_{fasta_file_basename}.{self.__get_output_key().lower()}'

    def __set_output(self) -> None:
        """
        Sets the output.
        :return: None
        """
        output_filename = self.folder / self.__get_output_filename()
        self._tool_outputs[self.__get_output_key()] = [ToolIOFile(output_filename)]

    def _check_command_output(self) -> None:
        """
        Checks the command output for errors.
        :return: None
        """
        if 'error' in self.stderr.lower() or self._command.returncode != 0:
            raise ToolExecutionError(f"Error executing {self.name}: {self._command.stderr.strip()}")

    def get_version(self) -> str:
        """
        Returns the version of the tool.
        :return: Tool version
        """
        command = Command(f'{self._tool_command} -version')
        command.run(Path().cwd())
        return re.search(f'blast[\w_]+: (.*)', command.stdout).group(1).strip()
