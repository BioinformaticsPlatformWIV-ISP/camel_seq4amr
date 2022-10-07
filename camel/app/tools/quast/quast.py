from pathlib import Path

from camel.app.error.invalidinputspecificationerror import InvalidInputSpecificationError
from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.tool import Tool


class Quast(Tool):

    """
    QUAST evaluates genome assemblies. QUAST works both with and without a reference genome. The tool accepts multiple
    assemblies, thus is suitable for comparison.
    """

    def __init__(self) -> None:
        """
        Initialize tool
        :return: None
        """
        super().__init__('quast', '5.2.0')

    def _execute_tool(self) -> None:
        """
        Runs Quast
        :return: None
        """
        self.__build_command()
        self._execute_command()
        self.__set_output()

    def _check_input(self) -> None:
        """
        Checks whether the given inputs are valid:
        - FASTA is required
        - FASTA_Ref, TSV_Gene, and TSV_Operon are optional
        - Only one input file allowed for FASTA_Ref, TSV_Gene, and TSV_Operon, multiple files allowed for FASTA
        :return: None
        """
        super(Quast, self)._check_input()
        if 'FASTA' not in self._tool_inputs:
            raise InvalidInputSpecificationError(
                f'QUAST required FASTA input is missing: {self._tool_inputs!r}')
        for key, values in self._tool_inputs.items():
            if key not in ['FASTA', 'FASTA_Ref', 'TSV_Gene', 'TSV_Operon']:
                raise InvalidInputSpecificationError(
                    f'Illegal input key given for QUAST: {self._tool_inputs!r}')
            if key in ['FASTA_Ref', 'TSV_Gene', 'TSV_Operon'] and len(values) > 1:
                raise InvalidInputSpecificationError(
                    f'Too many input files given for QUAST: {self._tool_inputs!r}')

    def __build_command(self) -> None:
        """
        Concatenates required parameters and options to build the command.
        :return: None
        """
        options_string = ' '.join(self._build_options() + [f'-o {self._folder}'])
        input_string = self.__build_input_string()
        self._command.command = ' '.join([self._tool_command, options_string, input_string])

    def __build_input_string(self) -> str:
        """
        Creates the string with the input files
        :return: String with the input parameters
        """
        inputs = []
        if 'FASTA_Ref' in self._tool_inputs:
            inputs.append(f"-R {self._tool_inputs['FASTA_Ref'][0].path}")
        if 'TSV_Gene' in self._tool_inputs:
            inputs.append(f"-G {self._tool_inputs['TSV_Gene'][0].path}")
        if 'TSV_Operon' in self._tool_inputs:
            inputs.append(f"-O {self._tool_inputs['TSV_Operon'][0].path}")
        for item in self._tool_inputs['FASTA']:
            inputs.append(str(item.path))
        return ' '.join(inputs)

    def _check_command_output(self) -> None:
        """
        Checks if the command was executed successfully.
        :return: None
        """
        for line in self.stderr.splitlines():
            if 'ERROR' in line:
                if 'ERRORs: 0' not in line:
                    raise ToolExecutionError(f"Command execution failed (stderr: {self.stderr}).")
        if self._command.returncode != 0:
            raise ToolExecutionError(f"Command execution failed (Exit code: {self._command.returncode})")

    def __set_output(self) -> None:
        """
        Sets the name of the output files
        :return: None
        """
        output_keys = ['HTML', 'TEX', 'TSV', 'TXT']
        for key in output_keys:
            self._tool_outputs[key] = [ToolIOFile(Path(f'{self.folder / "report"}.{key.lower()}'))]
        # for icarus browser
        icarus_output_keys = {
            'HTML_icarus': 'icarus.html',
            'HTML_alignment_viewer': 'icarus_viewers/alignment_viewer.html',
            'HTML_contig_size_viewer': 'icarus_viewers/contig_size_viewer.html'
        }
        for key, value in icarus_output_keys.items():
            if key == 'HTML_alignment_viewer' and 'FASTA_Ref' not in self._tool_inputs:
                # skip HTML_alignment_viewer when no reference genome is provided
                continue
            self._tool_outputs[key] = [ToolIOFile(self.folder / value)]
