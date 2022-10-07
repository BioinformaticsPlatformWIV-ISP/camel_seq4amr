import os

from camel.app.io.tooliovalue import ToolIOValue
from camel.app.tools.bowtie2.bowtie2 import Bowtie2
from camel.app.utils.fileutils import FileUtils


class Bowtie2Index(Bowtie2):

    """
    Index genome using 'bowtie2-build' cmd of Bowtie2
    """

    MULTI_FASTA_GENOME_FILE = 'complete_genome.fasta'

    def __init__(self) -> None:
        """
        Initialize bowtie2 index
        :return: None
        """
        super(Bowtie2Index, self).__init__('bowtie2 index', '2.4.1')
        self._refgenome_fasta = None

    def _execute_tool(self) -> None:
        """
        Function to run BWA index
        :return: None
        """
        self.__set_input()
        self.__build_command()
        self._execute_command()
        self.__set_output()

    def __get_multi_fasta_genome_filename(self) -> str:
        """
        Get the filename used for multi fasta file representing complete genome
        :return: name of the multi fasta file with complete path
        """
        return os.path.join(self._folder, Bowtie2Index.MULTI_FASTA_GENOME_FILE)

    def _check_input(self) -> None:
        """
        Check FASTA_REF input and concatenate them if multiple fasta input files
        :return: None
        """
        super(Bowtie2Index, self)._check_input()

        if len(self._tool_inputs['FASTA_REF']) == 0:
            raise ValueError("Required reference genome (FASTA) input file is missing.")

    def __set_input(self) -> None:
        """
        Set the input
        :return: None
        """
        nb_of_inputs = len(self._tool_inputs['FASTA_REF'])

        if nb_of_inputs > 1:
            multifasta_file = self.__get_multi_fasta_genome_filename()
            FileUtils.concatenate_files(multifasta_file, [f.path for f in self._tool_inputs['FASTA_REF']])
            self._refgenome_fasta = multifasta_file
        else:
            self._refgenome_fasta = os.path.join(self._folder, self._tool_inputs['FASTA_REF'][0].basename)
            if self._refgenome_fasta != self._tool_inputs['FASTA_REF'][0].path and not os.path.exists(
                    self._refgenome_fasta):
                os.symlink(self._tool_inputs['FASTA_REF'][0].path, self._refgenome_fasta)

    def __set_output(self) -> None:
        """
        Set output for bowtie2 index
        :return: None
        """
        self._tool_outputs['INDEX_GENOME_PREFIX'] = [ToolIOValue(self._refgenome_fasta)]

    def __build_command(self) -> None:
        """
        Build the command to run bowtie2 index
        :return: None
        """
        # Note the refgenome fasta name is used as index base
        options = ' '.join(self._build_options())
        self._command.command = f'{self._tool_command} {options} {self._refgenome_fasta} {self._refgenome_fasta}'
