import logging
from pathlib import Path

from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.io.tooliofile import ToolIOFile
from camel.app.io.tooliovalue import ToolIOValue
from camel.app.tools.tool import Tool


class Srst2Mlst(Tool):
    """
    This program is designed to take Illumina sequence data, a MLST database and/or a database of gene sequences
    (e.g. resistance genes, virulence genes, etc) and report the presence of subtypes and/or reference genes.
    """

    def __init__(self) -> None:
        """
        Initialize SRST2 MLST tool.
        """
        super().__init__('SRST2_MLST', '0.2.0')

    def _execute_tool(self):
        """
        Executes this tool.
        :return: None
        """
        self._command.command = self.__build_command()
        self._execute_command()
        self.__set_output()

    def __build_command(self):
        """
        Builds the command line command.
        :return: Command line command
        """
        return ' '.join([self._tool_command,
                         self.__build_input_string(),
                         self.__build_database_string(),
                         ' '.join(self._build_options())])

    def __build_input_string(self):
        """
        Builds a string containing the input.
        :return: Input options string
        """
        if 'FASTQ_PE' in self._tool_inputs:
            return '--input_pe {}'.format(' '.join([str(f.path) for f in self._tool_inputs['FASTQ_PE']]))
        else:
            return '--input_se {}'.format(self._tool_inputs['FASTQ_SE'][0].path)

    def __build_database_string(self):
        """
        Builds a string containing the database arguments.
        :return: Database options string
        """
        string = '--mlst_db {}'.format(self._tool_inputs['FASTA'][0].path)
        if 'TSV' in self._tool_inputs:
            string += ' --mlst_definitions {}'.format(self._tool_inputs['TSV'][0].path)
        return string

    def __set_output(self):
        """
        Sets the output files.
        :return: None
        """
        for file_ in self.folder.iterdir():
            key = self._get_output_file_key(file_)
            if key is not None:
                self._tool_outputs[key] = [ToolIOFile(file_)]
        self._tool_outputs['VAL_Sequence_type'] = [
            ToolIOValue(Srst2Mlst.__get_sequence_type(self._tool_outputs['TSV'][0].path))]

    def _check_input(self):
        """
        Checks whether the given inputs are valid.
        - FASTQ_PE or FASTQ_SE reads are required (checked by super class)
        - FASTA file with allele sequences is required
        - MLST file with sequence type definitions is optional
        """
        super(Srst2Mlst, self)._check_input()
        if 'FASTA' not in self._tool_inputs:
            raise IOError('No FASTA file with MLST alleles found.')
        if 'TSV' not in self._tool_inputs:
            logging.info("No MLST definitions found. Only performing allele detection.")

    def _get_output_file_key(self, path_in: Path) -> str:
        """
        Returns the key for the given output file.
        :param path_in: Output file path
        :return: Key
        """
        output_filename = self._parameters['output_filename'].value
        if all([x in path_in.name for x in ['mlst', 'results']]):
            return 'TSV'
        elif path_in.name.endswith('.pileup') and path_in.name.startswith(output_filename):
            return 'PILEUP'
        elif path_in.name.endswith('.bam'):
            return 'BAM'
        elif path_in.name.endswith('.scores'):
            return 'TSV_Scores'
        elif path_in.name.endswith('consensus_alleles.fasta'):
            return 'FASTA'

    @staticmethod
    def __get_sequence_type(output_file: Path) -> str:
        """
        Parses the output file to obtain the sequence type.
        :param output_file: Output file
        :return: Sequence type
        """
        with output_file.open() as handle:
            content = handle.readlines()
            if len(content) == 1:
                return 'ND'
            elif len(content) == 2:
                return content[1].split('\t')[1]
            raise ValueError("Invalid SRST2 output file. Content: '{}'".format(content))

    def _check_command_output(self) -> None:
        """
        Checks if the command execution was successful.
        :return: None
        """
        if 'SRST2 has finished' not in self.stderr.splitlines()[-1]:
            raise ToolExecutionError("SRST2 execution failed: {}".format(self.stderr))
