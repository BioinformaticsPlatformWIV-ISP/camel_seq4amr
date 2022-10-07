from camel.app.error.invalidparametererror import InvalidParameterError
from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.samtools.samtoolsbasepipeable import SamtoolsBasePipeable
from camel.app.utils.command import Command


class SamtoolsMPileup(SamtoolsBasePipeable):
    """
    Multi-way pileup.
    Notes:
    - VCF outputs are always bgzipped.
    """

    def __init__(self) -> None:
        """
        Initializes this tool.
        """
        super().__init__('samtools mpileup', '1.9')

    def _check_parameters(self) -> None:
        """
        Checks the parameters.
        :return: None
        """
        if self._parameters['output_format'].value not in ['pileup', 'vcf', 'bcf']:
            raise InvalidParameterError(f"Invalid output format: {self._parameters['output_format'].value}")
        super(SamtoolsMPileup, self)._check_parameters()

    def _check_input(self) -> None:
        """
        Checks the input.
        :return: None
        """
        if 'BAM' not in self._tool_inputs:
            raise ValueError("No BAM input file found")
        super(SamtoolsBasePipeable, self)._check_input()

    def _execute_tool(self) -> None:
        """
        Executes this tool.
        :return: None
        """
        self.__build_command()
        self._execute_command()
        self.__set_output()

    def __build_command(self, pipe_in: bool = False, pipe_out: bool = False) -> None:
        """
        Builds the command.
        :return: None
        """
        # Initialize command
        command_parts = [self._tool_command]

        # Add input
        if pipe_in:
            command_parts.append("/dev/stdin")
        else:
            command_parts.append(' '.join(str(f.path) for f in self._tool_inputs['BAM']))

        # Add optional inputs
        if 'FASTA' in self._tool_inputs:
            command_parts.append(f'--fasta-ref {self._tool_inputs["FASTA"][0].path}')
        if 'TXT_RG' in self._tool_inputs:
            command_parts.append(f'--exlude-RG {self._tool_inputs["TXT_RG"][0].path}')
        if 'TXT_POS' in self._tool_inputs:
            command_parts.append(f'--positions {self._tool_inputs["TXT_POS"][0].path}')

        # Add output format
        if not pipe_out:
            command_parts.extend(self._build_options(['output_format']))
            if self._parameters['output_format'].value == 'vcf':
                command_parts.append('--VCF')
            elif self._parameters['output_format'].value == 'bcf':
                command_parts.append('--BCF')

        # Construct command
        self._command.command = ' '.join(command_parts)

    def __set_output(self) -> None:
        """
        Sets the output of this tool.
        :return: None
        """
        output_files = {
            'vcf': ('VCF_GZ', self.folder / self._parameters['output_filename'].value),
            'bcf': ('BCF', self.folder / self._parameters['output_filename'].value),
            'pileup': ('PILEUP', self.folder / self._parameters['output_filename'].value)
        }
        key, path = output_files.get(self._parameters['output_format'].value)
        self._tool_outputs[key] = [ToolIOFile(path)]

    def _check_command_output(self) -> None:
        """
        Checks the command output.
        Supersedes function in Tool class because warnings printed to stderr can cause false abort.
        """
        self._check_stderr()

        if self._command.returncode != 0:
            raise ToolExecutionError(f"Command execution failed (Exit code: {self._command.returncode})")

    def _before_pipe(self, dir_, pipe_in: bool, pipe_out: bool) -> None:
        """
        Prepares the command that will be piped.
        :param dir_: Running directory
        :param pipe_in: True if tool receives piped input
        :param pipe_out: True if tool generates piped output
        :return: None
        """
        self.__build_command(pipe_in, pipe_out)

    def _after_pipe(self, stderr: str, is_last_in_pipe: bool) -> None:
        """
        Performs the required steps after executing the tool as part of a pipe.
        :param stderr: Stderr for this command in the pipe
        :param is_last_in_pipe: Boolean to indicate if this is the last step in the pipe
        :return: None
        """
        if is_last_in_pipe:
            self.__set_output()
