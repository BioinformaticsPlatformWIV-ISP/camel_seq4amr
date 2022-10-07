from pathlib import Path
from typing import Dict, Union, List

from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.tool import Tool


class FastQC(Tool):

    """
    FastQC tool.
    """

    def __init__(self) -> None:
        """
        Initializes FastQC.
        """
        super().__init__('FastQC', '0.11.5')

    def _execute_tool(self) -> None:
        """
        Runs FastQC.
        :return: None
        """
        self.__build_command()
        self._execute_command()
        self.__set_output()

    def _check_input(self) -> None:
        """
        Checks if the input is valid.
        :return: None
        """
        if 'FASTQ' not in self._tool_inputs or len(self._tool_inputs['FASTQ']) == 0:
            raise ValueError("Required FASTQ input file is missing for FastQC.")
        super(FastQC, self)._check_input()

    def __build_command(self) -> None:
        """
        Builds the command line call to execute FastQC.
        :return: None
        """
        self._command.command = ' '.join([
            self._tool_command,
            ' '.join(str(in_file) for in_file in self._tool_inputs['FASTQ']),
            '--outdir .',
            ' '.join(self._build_options())])

    def _check_command_output(self) -> None:
        """
        Checks if the command output is valid.
        :return: None
        """
        if not self._command.returncode == 0:
            raise ToolExecutionError(f"Error executing {self.name}: {self._command.stderr}")

    @staticmethod
    def __get_output_folder(execution_folder: Path, input_file: ToolIOFile) -> Path:
        """
        Returns the output folder for the given input file.
        :param execution_folder: Folder where the command is executed
        :param input_file: Input file name
        :return: Output folder
        """
        stem = input_file.path.stem
        suffix = input_file.path.suffix
        if suffix != '.fastq':
            # compressed file, XXXX.fastq.gz or XXXX.fastq.bz2
            stem = Path(stem).stem
        for sub_folder in execution_folder.glob('*'):
            if sub_folder.name.startswith(stem) and sub_folder.name.endswith('_fastqc'):
                full_path = execution_folder / sub_folder
                if full_path.is_dir():
                    return full_path
        raise IOError(f"No output directory for FastQC input {input_file} found.")

    @staticmethod
    def _analyze_summary_file(summary_file: Path) -> Dict[str, Union[bool, List[str]]]:
        """
        Analyze fastqc output summary.txt (of a given input file)
        :param summary_file: FastQC summary file
        :return: Dictionary containing the summary information
        """
        summary_info = {'passed': True, 'warnings': [], 'fails': []}
        with summary_file.open('r') as input_handle:
            for line in input_handle.readlines():
                status, test_name, _ = line.split('\t')
                if status == 'WARN':
                    summary_info['warnings'].append(test_name)
                elif status == 'FAIL':
                    summary_info['fails'].append(test_name)
        if len(summary_info['fails']) > 0:
            summary_info['passed'] = False
        return summary_info

    def __set_output(self) -> None:
        """
        Set the output of FastQC.
        :return: None
        """
        self._tool_outputs['HTML'] = []
        self._tool_outputs['TXT'] = []
        for input_file in self._tool_inputs['FASTQ']:
            output_folder = self.__get_output_folder(self.folder, input_file)
            self.informs[str(input_file)] = FastQC._analyze_summary_file(output_folder / 'summary.txt')
            for output_file in output_folder.glob('*'):
                if output_file.name == 'fastqc_report.html':
                    self._tool_outputs['HTML'].append(ToolIOFile(output_folder / output_file))
                elif output_file.name == 'fastqc_data.txt':
                    self._tool_outputs['TXT'].append(ToolIOFile(output_folder / output_file))
