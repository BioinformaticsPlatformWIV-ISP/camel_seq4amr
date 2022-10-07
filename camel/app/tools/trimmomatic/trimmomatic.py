import logging
import re
from pathlib import Path
from typing import List, Optional

from camel.app import loggingutils
from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.tool import Tool
from camel.app.utils.command import Command
from camel.app.utils.fastqutils import FastqUtils
from camel.app.utils.fileutils import FileUtils


class Trimmomatic(Tool):

    """
    A flexible read trimming tool for Illumina NGS Data.
    """

    def __init__(self) -> None:
        """
        Initializes Trimmomatic.
        """
        super().__init__('Trimmomatic', '0.38')
        self.__get_adapter_dir()
        self._mode = None

    def _execute_tool(self) -> None:
        """
        Runs Trimmomatic.
        :return: None
        """
        self.__build_command()
        self._execute_command()
        self.__set_output()
        self.__set_informs()
        if not self._informs.get('succeed', 'False'):
            raise ToolExecutionError("Error running trimmomatic")

    def _check_input(self) -> None:
        """
        Checks the input.
        :return: None
        """
        if 'FASTQ_PE' in self._tool_inputs:
            self._mode = 'PE'
            if len(self._tool_inputs['FASTQ_PE']) != 2:
                raise ValueError("Paired end input requires exactly 2 files.")
        elif 'FASTQ_SE' in self._tool_inputs:
            self._mode = 'SE'
            if len(self._tool_inputs['FASTQ_SE']) != 1:
                raise ValueError("Single end input requires exactly 1 file.")
        else:
            raise ValueError("No FASTQ_PE of FASTQ_SE input found")
        super(Trimmomatic, self)._check_input()

    def __get_adapter_dir(self) -> Path:
        """
        Retrieves the directory with the Trimmomatic adapters.
        :return: Path to adapters directory
        """
        # Locate conda installation
        cmd_conda = Command('which conda')
        cmd_conda.run(self._folder)
        if cmd_conda.stdout == '':
            raise RuntimeError("conda not available in path")
        path_conda = Path(cmd_conda.stdout)
        dir_adapters = path_conda.parents[1] / 'share' / 'trimmomatic' / 'adapters'
        if not dir_adapters.exists():
            raise ValueError("Cannot retrieve path of the Trimmomatic adapters")
        logging.info(f'Trimmomatic adapter dir: {dir_adapters}')
        return dir_adapters

    def __build_command(self) -> None:
        """
        Builds the command.
        :return: None
        """
        if self._mode == 'PE':
            options = self.__build_pe_command()
        else:
            options = self.__build_se_command()
        options += self._build_options(
            excluded_parameters=['baseout', 'threads', 'illuminaclip_PE', 'illuminaclip_SE'], delimiter='')
        option_string = ' '.join(options)
        self._command.command = ' '.join([
            f'export TRIMMOMATIC_ADAPTER_DIR={self.__get_adapter_dir()};',
            self._tool_command, option_string
        ])

    def __build_se_command(self) -> List[str]:
        """
        Builds the command to run in single end mode.
        :return: Command options
        """
        options = [self._mode]
        if 'threads' in self._parameters:
            options.append(str(self._parameters['threads']))
        options.append(self._tool_inputs['FASTQ_SE'][0].path)
        if 'baseout' in self._parameters:
            options.append(str(self._parameters['baseout']))
        if 'illuminaclip_SE' in self._parameters:
            options.append(self._parameters['illuminaclip_SE'].option + self._parameters['illuminaclip_SE'].value)
        return options

    def __build_pe_command(self) -> List[str]:
        """
        Builds the command to run in paired end mode.
        :return: Command options
        """
        options = [self._mode]
        if 'baseout' in self._parameters:
            options.append(str(self._parameters['baseout']))
        if 'threads' in self._parameters:
            options.append(str(self._parameters['threads']))
        options.append(' '.join(str(f) for f in self._tool_inputs['FASTQ_PE']))
        if 'illuminaclip_PE' in self._parameters:
            options.append(self._parameters['illuminaclip_PE'].option + self._parameters['illuminaclip_PE'].value)
        return options

    def __get_output_path(self, suffix: Optional[str]) -> Path:
        """
        Returns the path for the output file with the given suffix.
        """
        basename = re.search(r'(.*)\.fastq(.gz)?', Path(self._parameters['baseout'].value).name).group(1)
        is_gzipped = self._parameters['baseout'].value.endswith('.gz')
        if suffix is not None:
            return self.folder / f"{FileUtils.make_valid(basename)}_{suffix}.fastq{'.gz' if is_gzipped else ''}"
        return self.folder / f"{FileUtils.make_valid(basename)}.fastq{'.gz' if is_gzipped else ''}"

    def __set_output(self) -> None:
        """
        Sets the output of this tool.
        :return: None
        """

        if self._mode == 'PE':
            self._tool_outputs['FASTQ_PE'] = [
                ToolIOFile(self.__get_output_path('1P')), ToolIOFile(self.__get_output_path('2P'))]
            self._tool_outputs['FASTQ_SE_FORWARD'] = [ToolIOFile(self.__get_output_path('1U'))]
            self._tool_outputs['FASTQ_SE_REVERSE'] = [ToolIOFile(self.__get_output_path('2U'))]
        else:
            self._tool_outputs['FASTQ'] = [ToolIOFile(self.__get_output_path(None))]
        self.__remove_empty_outputs()

    def __remove_empty_outputs(self) -> None:
        """
        Removes the empty files from the outputs.
        :return: None
        """
        for key in self._tool_outputs:
            self._tool_outputs[key] = [
                tool_io for tool_io in self._tool_outputs[key] if FastqUtils.count_reads(tool_io.path) > 0]

    def __set_informs(self) -> None:
        """
        Adds the trimming statistics to the informs.
        :return: None
        """
        self._informs['mode'] = self._mode
        for line in self.stderr.splitlines():
            qc_encoding = re.search("Quality encoding detected as (?P<encode>\\w+)", line)
            if qc_encoding:
                self._informs['encoding'] = qc_encoding.group('encode')
            elif re.match("Input Read Pairs", line):
                res = re.match(r"Input Read Pairs: (\d+) Both Surviving: (\d+ \([\d.%]+\)) "
                               r"Forward Only Surviving: (\d+ \([\d.%]+\)) "
                               r"Reverse Only Surviving: (\d+ \([\d.%]+\)) "
                               r"Dropped: (\d+ \([\d.%]+\))", line)
                self._informs['paired_reads_in'] = res.groups()[0]
                self._informs['paired_reads_out'] = res.groups()[1]
                self._informs['forward_only_reads'] = res.groups()[2]
                self._informs['reverse_only_reads'] = res.groups()[3]
                self._informs['reads_drop'] = res.groups()[4]
            elif re.match('Input Read', line):
                res = re.match(r"Input Reads: (\d+) "
                               r"Surviving: (\d+ \([\d.%]+\)) "
                               r"Dropped: (\d+ \([\d.%]+\))", line)
                self._informs['reads_in'] = res.groups()[0]
                self._informs['reads_out'] = res.groups()[1]
                self._informs['reads_drop'] = res.groups()[2]
            elif line.strip() == 'Exit status: 0':
                self._informs['succeed'] = True

    def _check_command_output(self) -> None:
        """
        Checks if the command was executed successfully.
        :return: None
        """
        if not self._command.returncode == 0:
            raise ToolExecutionError(f"Error executing Trimmomatic: {self._command.stderr}")


if __name__ == '__main__':
    loggingutils.initialize_logging()
    trimmomatic = Trimmomatic()
    trimmomatic.add_input_files({
        'FASTQ_PE': [
            ToolIOFile(Path('/testdata/camel/workflows/trimming/reads_1.fastq')),
            ToolIOFile(Path('/testdata/camel/workflows/trimming/reads_2.fastq')),
        ]
    })
    trimmomatic.run(Path('/temp'))
