import logging
from pathlib import Path

from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.seqtk.seqtk import Seqtk
from camel.app.utils.fastqutils import FastqUtils
from camel.app.utils.fileutils import FileUtils


class SeqtkSubsample(Seqtk):

    """
    Class that subsamples fastq/fasta file(s) using seqkt
    """

    def __init__(self) -> None:
        """
        Initialize seqtk subsample
        :return: None
        """
        super().__init__('Seqtk Subsample', '1.3')
        self._supported_inputs = ['FASTA', 'FASTQ', 'FASTA_PE', 'FASTQ_PE']
        self._function_name = 'Subsample'
        self._specific_parameters = ['combine_output', 'output_prefix', 'fraction']
        self._output_files = []

    def _execute_tool(self) -> None:
        """
        Function to run seqtk subsample
        :return: None
        """
        self.__set_cmd_output()
        logging.debug(f"Seqtk Subsample input informs: input_mode {self.input_mode}, input_file_type {self.input_file_type}")
        for idx, infile in enumerate(self._tool_inputs[self.input_type]):
            self.__build_command_with_iofiles(infile.path, self._output_files[idx])
            self._execute_command()
        self._set_output()
        self._set_informs()

    def __set_cmd_output(self) -> None:
        """
        Set the output specification for run seqtk subsample command
        :return: None
        """
        output_file_prefix = self._parameters['output_prefix'].value
        output_suffix = self.__get_output_file_suffix()

        if self.input_mode == 'SE':
            self._output_files = [self.folder / (output_file_prefix + output_suffix)]
        elif self.input_mode == 'PE':
            self._output_files = [
                self.folder / (output_file_prefix + "_1" + output_suffix),
                self.folder / (output_file_prefix + "_2" + output_suffix)
            ]

    def __build_command_with_iofiles(self, input_file: Path, output_file: Path) -> None:
        """
        Build the command to seqtk subsample
        :param input_file:
        :param output_file:
        :return: None
        """
        self._command.command = "{} {} {} {} > {}".format(
            self._tool_command,
            " ".join(self._build_options(excluded_parameters=self._specific_parameters)),
            input_file,
            self._parameters['fraction'].value,
            output_file
        )

    def _set_output(self) -> None:
        """
        Set self._tool_outputs specification
        """
        if self.input_mode == 'PE':
            self.__set_pe_outputs()
        else:
            self.__set_se_output()

    def __set_se_output(self) -> None:
        """
        Set self._tool_outputs specification for SE mode
        """
        self._tool_outputs[self.input_file_type] = [ToolIOFile(self._output_files[0])]

    def __set_pe_outputs(self) -> None:
        """
        Set self._tool_output for PE mode
        :return: None
        """
        # for PE mode, final output depend on combine_output option
        if 'combine_output' in self._parameters:
            # Tag if set: combine outputs of individual PE reads into one file
            output_file = self.folder / (self._parameters['output_prefix'].value + self.__get_output_file_suffix())
            FileUtils.concatenate_files(output_file, self._output_files)
            self._tool_outputs[self.input_file_type] = [ToolIOFile(output_file)]
        else:
            self._tool_outputs[self.input_file_type + '_PE'] = [ToolIOFile(f) for f in self._output_files]

    def __get_output_file_suffix(self) -> str:
        """
        Obtain the file's suffix based on input file type
        :return: string, filename suffix
        """
        if self.input_file_type == 'FASTA':
            return '.fa'
        elif self.input_file_type == 'FASTQ':
            return '.fq'
        else:
            raise ValueError("Seqtk Subsample supports only FASTA/FASTQ as input.")

    def _set_informs(self):
        """
        Analyze resulting reads file and report reads count in informs
        :return: None
        """
        if self.input_mode == 'PE':
            if 'combine_output' in self._parameters:
                self._informs['reads_count'] = FastqUtils.count_reads(self._tool_outputs[self.input_file_type][0].path)
            else:
                reads_count_per_file = [FastqUtils.count_reads(f.path) for f in self._tool_outputs[self.input_file_type+'_PE']]
                self._informs['reads_count'] = sum(reads_count_per_file)
        elif self.input_mode == 'SE':
            self._informs['reads_count'] = FastqUtils.count_reads(self._tool_outputs[self.input_file_type][0].path)
