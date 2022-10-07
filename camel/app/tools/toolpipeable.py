from pathlib import Path

import abc

from camel.app.tools.tool import Tool
from camel.app.utils.command import Command


class ToolPipeable(Tool, metaclass=abc.ABCMeta):
    """
    Contains the common functionality of tools.
    """

    def _before_pipe(self, path_pipe_in: Path, pipe_in: bool, pipe_out: bool) -> None:
        """
        Performs the required steps before executing the tool as part of a pipe.
        :param pipe_in: True if tool receives piped input
        :param pipe_out: True if tool generates piped output
        :return: None
        """
        raise NotImplementedError("Should be implemented")

    def _after_pipe(self, stderr: str, is_last_in_pipe: bool) -> None:
        """
        Performs the required steps after executing the tool as part of a pipe.
        :param is_last_in_pipe: Boolean to indicate if this is the last step in the pipe
        :return: None
        """
        raise NotImplementedError("Should be implemented")

    def prepare_pipe(self, dir_: Path, pipe_in: bool, pipe_out: bool) -> Command:
        """
        Creates the command that should be executed in the pipe.
        :param dir_: Working directory
        :param pipe_in: True if tool receives piped input
        :param pipe_out: True if tool generates piped output
        :return: Command that should be piped
        """
        self._folder = dir_
        # Check the input at the start of the python
        if pipe_in is False:
            self._check_input()

        # Return the command
        self._before_pipe(dir_, pipe_in, pipe_out)
        return self._command

    def process_pipe(self, stderr: str, is_last: bool) -> None:
        """
        Processes the pipe output.
        :param stderr: Standard error
        :param is_last: Boolean to indicate if this is the last step in the pipe
        :return: None
        """
        self._after_pipe(stderr, is_last)
