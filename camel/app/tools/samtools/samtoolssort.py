from camel.app.error.invalidparametererror import InvalidParameterError
from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.samtools.samtoolsbasepipeable import SamtoolsBasePipeable


class SamtoolsSort(SamtoolsBasePipeable):
    """
    Sorts alignment files.
    """

    def __init__(self) -> None:
        """
        Initializes this tool.
        """
        super().__init__('samtools sort', '1.9')

    def _check_input(self) -> None:
        """
        Checks the input.
        :return: None
        """
        if 'BAM' not in self._tool_inputs:
            raise ValueError("No BAM input file found")
        super(SamtoolsBasePipeable, self)._check_input()

    def _check_parameters(self) -> None:
        """
        Checks the tool parameters.
        :return: None
        """
        if self._parameters['output_format'].value.upper() not in ('SAM', 'BAM'):
            raise InvalidParameterError("Invalid output format (BAM/SAM supported)")
        super(SamtoolsSort, self)._check_parameters()

    def _execute_tool(self) -> None:
        """
        Executes this tool.
        :return: None
        """
        self.__build_command()
        self._execute_command()
        self.__set_output()
        self._check_stderr()

    def __build_command(self, pipe_in: bool = False, pipe_out: bool = False) -> None:
        """
        Builds the command
        :return: None
        """
        # Create excluded parameters
        excluded_params = ['output_filename'] if (pipe_out is True) else None

        # Construct command
        command_parts = [
            self._tool_command,
            ' '.join(self._build_options(excluded_parameters=excluded_params))
        ]

        # Add input file
        if not pipe_in:
            command_parts.append(str(self._tool_inputs['BAM'][0].path))

        # Construct command
        self._command.command = ' '.join(command_parts)

    def __set_output(self) -> None:
        """
        Sets the tool output.
        :return: None
        """
        output_path = self.folder / self._parameters['output_filename'].value
        if not output_path.is_file():
            raise ToolExecutionError(f"Expected {self._name} output not generated")
        output_key = self._parameters['output_format'].value.upper()
        self._tool_outputs[output_key] = [ToolIOFile(output_path)]

    def _check_command_output(self) -> None:
        """
        Checks if the command was executed successfully. Supersedes that of Tool class as samtools prints warnings to stderr.
        :return: None
        """
        if self._command.returncode != 0:
            raise ToolExecutionError("Command execution failed (Exit code: {})".format(self._command.returncode))

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
