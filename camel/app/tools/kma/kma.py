from pathlib import Path

from camel.app.error.invalidinputspecificationerror import InvalidInputSpecificationError
from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.tool import Tool


class KMA(Tool):
    """
    KMA is mapping a method designed to map raw reads directly against redundant databases, in an ultra-fast manner
    using seed and extend.
    """

    def __init__(self) -> None:
        """
        Initializes this tool.
        """
        super().__init__('KMA', '1.2.25')

    def _check_input(self) -> None:
        """
        Checks if the provided input is valid.
        :return: None
        """
        if not(any(x in self._tool_inputs for x in ['FASTQ_PE', 'FASTQ_SE'])):
            raise InvalidInputSpecificationError('FASTQ(PE|SE) input is required')
        if 'DB' not in self._tool_inputs:
            raise InvalidInputSpecificationError('DB input is required')
        super()._check_input()

    def _execute_tool(self) -> None:
        """
        Executes this tool.
        :return: None
        """
        self.__build_command()
        self._execute_command()
        self.__set_output()

    def __build_command(self) -> None:
        """
        Builds the command line call.
        :return: None
        """
        if 'FASTQ_PE' in self._tool_inputs:
            input_str = '-ipe {}'.format(' '.join(str(x.path) for x in self._tool_inputs['FASTQ_PE']))
        else:
            input_str = f"-i {self._tool_inputs['FASTQ_SE'][0].path}"
        self._command.command = ' '.join([
            self._tool_command,
            input_str,
            '-t_db {}'.format(self._tool_inputs['DB'][0].value)
        ] + self._build_options())

    def __set_output(self) -> None:
        """
        Collects the output generated by the tool.
        """
        output_base = self.folder / Path(self._parameters['output_basename'].value)
        for extension, key in [('aln', 'ALN'), ('fsa', 'FASTA'), ('res', 'TSV')]:
            p = output_base.parent / f'{output_base.name}.{extension}'
            if p.exists():
                self._tool_outputs[key] = [ToolIOFile(p)]

    def _check_command_output(self) -> None:
        """
        Checks if the tool was executed successfully.
        :return: None
        """
        if self._command.returncode != 0:
            raise ToolExecutionError(f'Error executing {self.name}: {self._command.stderr}')