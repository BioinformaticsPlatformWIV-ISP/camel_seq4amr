import logging
import re
from pathlib import Path
from typing import List, Dict

from camel.app.error.invalidinputspecificationerror import InvalidInputSpecificationError
from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.tool import Tool


class SPAdes(Tool):

    """
    SPAdes de novo short-reads or hybrid assembler, especially supports handling of single-cell (MDA) data utilizing its
    own reads error correction method
    """
    FASTA_CONTIG = 'contigs.fasta'
    FASTA_SCAFFOLDS = 'scaffolds.fasta'
    FASTG = 'assembly_graph.fastg'

    def __init__(self) -> None:
        """
        Initialize tool
        :return: None
        """
        super().__init__('spades', '3.13.0')
        self._input_string = None

    def _execute_tool(self) -> None:
        """
        Function to run SPAdes to do de novo assembly
        :return: None
        """
        self.__check_and_set_input()
        self.__build_command()
        self._execute_command()
        self.__set_output()

    @staticmethod
    def __compose_input_str(input_type: str, files: List[Path], ordinal: str = '0') -> str:
        """
        Compose input option string
        :param input_type: type of the input
        :param files: input files of given type
        :param ordinal: string represents the ordinal of the library, '0'=NA, '1'=1st, '2'=2nd, etc.
        :return: input option string of given input
        """
        input_type = input_type.lower()
        if input_type == 'se':
            return f"--s{ordinal} {files[0]}"

        elif input_type in ('pe', 'mp', 'hqmp'):
            return f"--{input_type}{ordinal}-1 {files[0]} --{input_type}{ordinal}-2 {files[1]}"

        elif input_type in ('pe-s', 'mp-s', 'hqmp-s'):
            input_type = input_type.split("-")[0]
            # unpaired reads from pe, mp, hqmp libraries
            return " ".join(["--{}{}-s {}".format(input_type, ordinal, f) for f in files])

        else:
            # other types: contigs, sanger, pacbio, nanopore
            return " ".join(["--{} {}".format(input_type, f) for f in files])

    @staticmethod
    def __check_shortreads_library_limitation(reads_type: str, count: int) -> None:
        """
        Check whether the number of libraries of given type exceed maximum (5)
        :param reads_type: the type of the library
        :param count: the identified number of libraries of a given type
        :return: None
        """
        if count > 5:
            raise InvalidInputSpecificationError(
                f"SPAdes does not support more than 5 libraries of input type {reads_type}, {count} are found.")

    @staticmethod
    def __check_min_input_requirement(se_count: int, pe_count: int, inputs: Dict[str, List[ToolIOFile]]):
        """
        Check whether the minimum input requirement, at least one library of type SE or PE
        :param se_count: number of SE libraries
        :param pe_count: number of PE libraries
        :param inputs: dictionary of input files
        """
        if se_count == 0 and pe_count == 0:
            raise InvalidInputSpecificationError(
                f"SPAdes requires at least one library of SE or PE read to work, none is found. tool_inputs: {inputs}")

    def __set_long_sequences(self, key_informs: List[str], files: List[Path], infiles_options: List[str]) -> bool:
        """
        Set long sequences part of the input specification
        :param key_informs: the information in the key of input file
        :param files: the corresponding files of a given key
        :param infiles_options: a list of input file specifications, updated if necessary
        :return: True if input type is recognized, otherwise False
        """
        if key_informs[1] == 'contigs':
            if key_informs[2] is not None:
                if key_informs[2] == 'untrusted':
                    # untrusted contigs
                    infiles_options.append(self.__compose_input_str('untrusted-contigs', files))
                else:
                    raise InvalidInputSpecificationError(
                        "Unsupported SPAdes contig input specification found {!r}. Supports only FAST{{Q/A}}_contigs("
                        "_untrusted).".format("_".join(key_informs)))
            else:
                # trusted contigs
                infiles_options.append(self.__compose_input_str('trusted-contigs', files))
            return True
        elif key_informs[1] in ('sanger', 'pacbio', 'nanopore'):
            # sanger, pacbio, or nanopore reads
            infiles_options.append(self.__compose_input_str(key_informs[1], files))
            return True
        else:
            return False

    def __check_and_set_input(self) -> None:
        """
        SPAdes specific input file checking and handling. For the supported input types check wiki.
        :return: None
        """
        infiles_options = []
        se_count = 0
        pe_count = 0
        mp_count = 0
        hqmp_count = 0
        for key in self._tool_inputs:

            key_informs = key.split("_")
            files = [f.path for f in self._tool_inputs[key]]

            # short reads: SE, PE, MP, HQMP, and their unpaired reads
            #              (PE-S, MP-S, HQMP-S)
            if key_informs[1] in {'SE', 'PE', 'PE-S', 'MP', 'MP-S'}:
                if len(key_informs) != 3:
                    raise InvalidInputSpecificationError(
                        "SPAdes input specification requires a strict format: {{FASTQ/FASTA}}_{{SE/PE/PE-S/MP/MP-S}}_"
                        "{{(HQ)1..5}}. Found an unsupported one {!r}.".format(key))

                res = re.match(r"HQ(\d)", key_informs[2])
                if res:
                    # HQMP reads
                    if key_informs[1] == 'MP':
                        key_informs[1] = 'HQMP'
                        hqmp_count += 1
                    else:
                        key_informs[1] = 'HQMP-S'
                else:
                    # SE, PE, MP reads
                    if key_informs[1] == 'SE':
                        se_count += 1
                    elif key_informs[1] == 'PE':
                        pe_count += 1
                    elif key_informs[1] == 'MP':
                        mp_count += 1

                if key_informs[1].lower() in ('pe', 'mp', 'hqmp'):
                    if len(files) != 2:
                        raise InvalidInputSpecificationError(
                            f"For input type {key_informs[1]!r}, SPAdes requirses two and only two files!")

                infiles_options.append(
                    self.__compose_input_str(key_informs[1], files, key_informs[2]))

            # long sequences
            elif not self.__set_long_sequences(key_informs, files, infiles_options):
                raise InvalidInputSpecificationError(f"Unsupported input library type {key!r} for SPAdes.")

        # check short reads library count (not more then 5)
        reads_types = ['se', 'pe', 'mp', 'hqmp']
        reads_types_count = [se_count, pe_count, mp_count, hqmp_count]
        list(map(
            self.__check_shortreads_library_limitation,
            reads_types,
            reads_types_count
        ))

        # check basic input requirement
        self.__check_min_input_requirement(se_count, pe_count, self._tool_inputs)

        self._input_string = " ".join(infiles_options)

    def __set_output(self) -> None:
        """
        Specify the output of tool and the command line options
        :return: None
        """
        output_dir = self._folder / self._parameters['output_dir'].value
        self.__check_and_set_output('FASTA_Contig', output_dir / SPAdes.FASTA_CONTIG)
        self.__check_and_set_output('FASTA_Scaffolds', output_dir / SPAdes.FASTA_SCAFFOLDS)
        self.__check_and_set_output('FASTG', output_dir / SPAdes.FASTG)

    def __check_and_set_output(self, output_key: str, output_file: Path):
        """
        Check the existance of output_file. Update self._tool_outputs only when file exists.
        :param output_key: output key to be set in self._tool_outputs
        :param output_file: output_file to be stored in self._tool_outputs
        :return: None
        """
        if not output_file.is_file():
            logging.warning(f"{output_key} file not generated.")
        else:
            self._tool_outputs[output_key] = [ToolIOFile(output_file)]

    def __build_command(self) -> None:
        """
        Build the command to run tool
        :return: None
        """
        self._command.command = " ".join([
            self._tool_command, self._input_string, " ".join(self._build_options())
        ])
