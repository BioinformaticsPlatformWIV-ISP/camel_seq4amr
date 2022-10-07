import abc

from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.tools.tool import Tool


class SamtoolsBase(Tool, metaclass=abc.ABCMeta):
    """
    Super class for samtools.
    """

    def __init__(self, tool_name: str, version: str) -> None:
        """
        Initialize a samtools tool.
        :param tool_name: Tool name
        :param version: Tool version
        :return: None
        """
        super().__init__(tool_name, version)

    def _execute_tool(self) -> None:
        """
        Executes this tool.
        :return: None
        """
        super(SamtoolsBase, self)._execute_tool()

    def _check_stderr(self) -> None:
        """
        Validate if the program ran correctly by checking the standard error.
        :return: None
        """
        if any(keyword in self._command.stderr.lower() for keyword in ('aborted', 'error')):
            raise ToolExecutionError(f"{self.name} failed: '{self._command.stderr}'")
