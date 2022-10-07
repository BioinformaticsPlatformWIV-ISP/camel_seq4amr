import re
from pathlib import Path
from typing import Tuple

from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.samtools.samtoolsbasepipeable import SamtoolsBasePipeable


class SamtoolsFlagstat(SamtoolsBasePipeable):
    """
    Calculates Simple BAM/SAM file statistics.
    """

    def __init__(self) -> None:
        """
        Initializes this tool.
        """
        super().__init__('samtools flagstat', '1.9')

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
        self._check_stderr()

    def __build_command(self, pipe_in: bool = False, pipe_out: bool = False) -> None:
        """
        Builds the command
        :return: None
        """
        command_parts = [self._tool_command]

        # Pipe input
        if not pipe_in:
            command_parts.append(str(self._tool_inputs['BAM'][0].path))
        else:
            command_parts.append('-')

        # Pipe output
        if (pipe_out is False) and ('output_filename' in self._parameters):
            output_filename = Path(self.folder) / self._parameters['output_filename'].value
            command_parts.append(f' > {output_filename}')

        self._command.command = ' '.join(command_parts)

    def __set_informs(self, output_file: Path) -> None:
        """
        Sets the informs for this tool.
        :return: None
        """
        with open(output_file) as filehandle:
            lines = filehandle.readlines()

            self._informs['total'] = SamtoolsFlagstat.__parse_output_line(lines[0])
            self._informs['secondary'] = SamtoolsFlagstat.__parse_output_line(lines[1])
            self._informs['supplementary'] = SamtoolsFlagstat.__parse_output_line(lines[2])
            self._informs['duplicates'] = SamtoolsFlagstat.__parse_output_line(lines[3])
            self._informs['mapped'] = SamtoolsFlagstat.__parse_output_line(lines[4])
            self._informs['paired'] = SamtoolsFlagstat.__parse_output_line(lines[5])
            self._informs['read1'] = SamtoolsFlagstat.__parse_output_line(lines[6])
            self._informs['read2'] = SamtoolsFlagstat.__parse_output_line(lines[7])
            self._informs['properly_paired'] = SamtoolsFlagstat.__parse_output_line(lines[8])
            self._informs['singletons'] = SamtoolsFlagstat.__parse_output_line(lines[10])

    @staticmethod
    def __parse_output_line(line: str) -> Tuple[int, int]:
        """
        Parses a line of flagstat output
        :param line: Flagstat output line
        :return: Line values
        """
        m = re.match(r'^(\d+) \+ (\d+).*', line)
        if m is None:
            raise ValueError(f"Cannot parse: '{line}'")
        return int(m.group(1)), int(m.group(2))

    def __set_output(self) -> None:
        """
        Sets the output of this tool.
        :return: None
        """
        output_path = self.folder / self._parameters['output_filename'].value
        self._tool_outputs['TXT'] = [ToolIOFile(output_path)]
        self.__set_informs(output_path)

    def _before_pipe(self, dir_, pipe_in: bool, pipe_out: bool) -> None:
        """
        Prepares the command that will be piped.
        :param dir_: Running directory
        :param pipe_in: True if tool receives piped input
        :param pipe_out: True if tool generates piped output
        :return: None
        """
        self.__build_command(pipe_in, pipe_out)

    def _after_pipe(self, stderr, is_last_in_pipe: bool) -> None:
        """
        Performs the required steps after executing the tool as part of a pipe.
        :param stderr: Stderr for this command in the pipe
        :param is_last_in_pipe: Boolean to indicate if this is the last step in the pipe
        :return: None
        """
        if is_last_in_pipe:
            self.__set_output()
