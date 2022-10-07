import logging
from pathlib import Path

from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.tool import Tool
from camel.app.utils.command import Command

PARAM_FMT_BY_NAME = {
    'max_divergence': {'title': 'Max. divergence', 'format': '{}%'},
    'max_mismatch': {'title': 'Max. nb. mismatches'},
    'min_coverage': {'title': 'Min. coverage', 'format': '{}%'},
    'min_depth': {'title': 'Min. depth', 'format': '{}x'}
}


class Srst2Gene(Tool):
    """
    This program is designed to take Illumina sequence data, a MLST database and/or a database of gene sequences
    (e.g. resistance genes, virulence genes, etc) and report the presence of subtypes and/or reference genes.
    """

    def __init__(self) -> None:
        """
        Initialize SRST2 Gene tool.
        """
        super(Srst2Gene, self).__init__('SRST2_Gene', '0.2.0')

    def _execute_tool(self) -> None:
        """
        Executes this tool.
        :return: None
        """
        self._command.command = self.__build_command()
        self._execute_command()
        self.__set_output()
        self.__set_informs()

    def __get_conda_init(self) -> Path:
        """
        Determines the location of the conda init script.
        :return: Path to conda init script.
        """
        # Locate conda installation
        cmd_conda = Command('which conda')
        cmd_conda.run(self._folder)
        if cmd_conda.stdout == '':
            raise RuntimeError("conda not available in path")
        path_conda = Path(cmd_conda.stdout)
        path_init = path_conda.parents[1] / 'etc' / 'profile.d' / 'conda.sh'
        if not path_init.exists():
            raise ValueError("Cannot retrieve path of the conda init script")
        return path_init

    def __build_command(self) -> str:
        """
        Builds the command line call.
        :return: Command line call
        """
        return ' '.join([
            f'. {self.__get_conda_init()};',
            self._tool_command,
            self.__build_input_string(),
            '--gene_db {}'.format(self._tool_inputs['FASTA'][0].path),
            ' '.join(self._build_options())])

    def __build_input_string(self) -> str:
        """
        Builds a string containing the input.
        :return: Input options string
        """
        if 'FASTQ_PE' in self._tool_inputs:
            return '--input_pe {}'.format(' '.join([str(f.path) for f in self._tool_inputs['FASTQ_PE']]))
        else:
            return '--input_se {}'.format(self._tool_inputs['FASTQ_SE'][0].path)

    def __set_output(self) -> None:
        """
        Sets the output files.
        :return: None
        """
        for file_ in Path(self._folder).iterdir():
            key = self._get_output_file_key(file_.name)
            if key is not None:
                self._tool_outputs[key] = [ToolIOFile(file_)]

    def __set_informs(self) -> None:
        """
        Sets the informs for this tool.
        :return: None
        """
        for param_name, param in self._parameters.items():
            if param_name not in PARAM_FMT_BY_NAME:
                continue
            fmt = PARAM_FMT_BY_NAME[param_name]
            self._informs[fmt['title']] = fmt.get('format', '{}').format(param.value)

    def _check_input(self) -> None:
        """
        Checks whether the given inputs are valid.
        - FASTQ_PE or FASTQ_SE reads are required (checked by super class)
        - FASTA file with allele sequences is required
        - MLST file with sequence type definitions is optional
        """
        super(Srst2Gene, self)._check_input()
        if 'FASTA' not in self._tool_inputs:
            raise IOError('No FASTA file with MLST alleles found.')
        if 'MLST' not in self._tool_inputs:
            logging.info("No MLST definitions found. Only performing allele detection.")

    def _get_output_file_key(self, filename: str) -> str:
        """
        Returns the key for the given output file.
        :param filename: Filename
        :return: Key
        """
        output_filename = self._parameters['output_filename'].value
        if all([x in filename for x in ['fullgenes', 'results']]):
            return 'TSV'
        elif filename.endswith('.pileup') and filename.startswith(output_filename):
            return 'PILEUP'
        elif filename.endswith('.bam'):
            return 'BAM'
        elif filename.endswith('.scores'):
            return 'TSV_Scores'
        elif filename.endswith('consensus_alleles.fasta'):
            return 'FASTA'

    def _check_command_output(self) -> None:
        """
        Checks if the command execution was successful.
        :return: None
        """
        if 'Could not determine forward/reverse read status' in self._command.stderr:
            raise ToolExecutionError("Invalid names for the FASTQ files")
        if self._command.returncode != 0:
            raise ToolExecutionError("SRST2 execution failed: {}".format(self.stderr))
