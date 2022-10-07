import logging
from pathlib import Path

from camel.app.error.invalidparametererror import InvalidParameterError
from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.samtools.samtoolsbase import SamtoolsBase


class SamtoolsFastaIndex(SamtoolsBase):
    """
    Indexes FASTA files.
    """

    def __init__(self) -> None:
        """
        Initializes this tool.
        """
        super().__init__('samtools faidx', '1.9')

    def _check_input(self) -> None:
        """
        Checks the input.
        :return: None
        """
        if 'FASTA' not in self._tool_inputs:
            raise ValueError("No FASTA input file found")
        if len(self._tool_inputs['FASTA']) != 1:
            raise ValueError("Only one FASTA input file is supported.")
        super(SamtoolsBase, self)._check_input()

    def _check_parameters(self) -> None:
        """
        Checks the parameters.
        :return: None
        """
        if 'regions' in self._parameters and 'output_filename' not in self._parameters:
            raise InvalidParameterError("Cannot extract regions without output filename")
        super(SamtoolsFastaIndex, self)._check_parameters()

    def __symlink_input(self) -> Path:
        """
        Creates a symlink for the input.
        :return: Path to the symlink of the input
        """
        symlink_location = self.folder / self._tool_inputs['FASTA'][0].path.name
        try:
            symlink_location.symlink_to(self._tool_inputs['FASTA'][0].path)
        except OSError:
            pass
        return symlink_location

    def _execute_tool(self) -> None:
        """
        Executes this tool.
        :return: None
        """
        fasta_file = self.__symlink_input()
        self.__build_command(fasta_file)
        self._execute_command()
        self._check_stderr()
        if 'regions' in self._parameters:
            self._tool_outputs['FASTA'] = [ToolIOFile(self.folder / self._parameters['output_filename'].value)]
        else:
            self._tool_outputs['FASTA'] = [ToolIOFile(fasta_file)]

    def __build_command(self, fasta_file: Path) -> None:
        """
        Builds the command for this tool.
        :param fasta_file: FASTA file
        :return: None
        """
        self._command.command = ' '.join([self._tool_command, str(fasta_file)])
        if 'output_filename' in self._parameters and 'regions' in self._parameters:
            logging.info("Extracting regions from FASTA file, file should already be indexed.")
            self._command.command += f" {self._parameters['regions'].value} > {self._parameters['output_filename'].value}"

    def _check_stderr(self) -> None:
        """
        Checks the command stderr output.
        :return: None
        """
        if 'build FASTA index' in self.stderr:
            raise ToolExecutionError("Cannot extract regions from an unindexed FASTA file.")
