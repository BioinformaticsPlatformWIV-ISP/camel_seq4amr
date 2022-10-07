import abc

from camel.app.error.invalidinputspecificationerror import InvalidInputSpecificationError
from camel.app.tools.tool import Tool


class Seqtk(Tool, metaclass=abc.ABCMeta):

    """
    Base class for all seqtk functionality
    """

    def __init__(self, tool_name: str, version: str) -> None:
        """
        Initialize seqtk
        :param tool_name: Tool name
        :param version: Tool version
        :return: None
        """
        super().__init__(tool_name, version)
        self._function_name = ''
        # parameters that should not be handled by self.build_options function
        self._specific_parameters = []
        # alternative types of files that can be used as main input of a seqtk tool
        # - FASTA or FASTQ
        self._supported_inputs = []  # Possible values: 'FASTA', 'FASTQ', 'FASTA_SE', 'FASTQ_SE', 'FASTA_PE', 'FASTQ_PE'
        self.input_type = None
        self.input_mode = None       # 'SE' or 'PE'
        self.input_file_type = None  # 'FASTQ' or 'FASTA'
        self._output_string = ''

    def _execute_tool(self) -> None:
        """
        Function to run Seqtk
        :return: None
        """
        self._set_output()
        self._build_command()
        self._execute_command()

    def _check_input(self) -> None:
        """
        Check input requirements to run seqtk
        :return: None
        """
        if len(self._supported_inputs) != 0:
            self.__set_input_type_and_mode()
            self.__check_supported_input_files()

    def __set_input_type_and_mode(self) -> None:
        """
        Check the type of supported_inputs (alternatives but still required) specified in _tool_inputs and set
        the input_type and input_mode variables.
        :return: None
        """
        for input_type in self._supported_inputs:
            if input_type in self._tool_inputs:
                self.input_type = input_type
                type_inform = input_type.split("_")
                if len(type_inform) > 1:
                    self.input_mode = type_inform[1]  # PE or SE
                else:
                    # by default, support only one input
                    self.input_mode = 'SE'
                self.input_file_type = type_inform[0]
                return

        raise KeyError(f'Seqtk function {self._function_name} required input is missing. Followings are supported: {self._supported_inputs}.')

    def __check_supported_input_files(self) -> None:
        """
        Check supported input files are correct
        :return: None
        """
        if self.input_mode == 'SE' and len(self._tool_inputs[self.input_type]) != 1:
            raise InvalidInputSpecificationError(
                f"Seqtk function {self._function_name} SE mode supports only one input file.")
        elif self.input_mode == 'PE' and len(self._tool_inputs[self.input_type]) != 2:
            raise InvalidInputSpecificationError(
                f"Seqtk function {self._function_name} PE mode supports only two input files.")

    @abc.abstractmethod
    def _set_output(self) -> None:
        """
        Set the output specification
        :return: None
        """
        pass

    def _get_input_string(self) -> None:
        """
        Returns the input string needed for the command
        :return: input_string containing input specification
        """
        pass

    def _build_command(self) -> None:
        """
        Build the command to run tool
        :return: None
        """
        self._command.command = "{} {} {} > {}".format(
            self._tool_command,
            " ".join(self._build_options(excluded_parameters=self._specific_parameters)),
            self._get_input_string(),
            self._output_string
        )
