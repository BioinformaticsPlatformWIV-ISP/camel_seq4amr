import re
from pathlib import Path
from typing import Optional
from typing import Set, List

from camel.app.error.invalidparametererror import InvalidParameterError
from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.bowtie2.bowtie2 import Bowtie2
from camel.app.utils.command import Command


class Bowtie2Map(Bowtie2):

    """
    Reads mapping using Bowtie2. It does **not** support using both PE and SE reads. Does **not** support interleaved
    fastq format due to lack of use.
    """
    OUTPUT_NAME = 'bowtie2_readmap.sam'
    DEFAULT_SAMPLE_NAME = 'sampleA'
    TIME_INFORM_MAPPING = {
        'Time loading reference': 'time_loading_reference',
        'Time loading forward index': 'time_loading_forward_index',
        'Time loading mirror index': 'time_loading_reverse_index',
        'Time searching': 'time_searching',
        'Multiseed full-index search': 'time_multiseed_full-index_search',
        'Overall time': 'time_total'
    }
    ALIGN_INFORM_MAPPING = {
        'were unpaired; ': 'stats_singe_reads_in',
        'were paired; ': 'stats_paired_reads_in',
        'aligned concordantly 0 times': 'stats_pair_0_concord_map',
        'aligned concordantly exactly 1 time': 'stats_pair_1_concord_map',
        'aligned concordantly >1 times': 'stats_pair_n_concord_maps',
        'aligned discordantly 1 time': 'stats_pair_disconcord_maps',
        'aligned 0 times': 'stats_single_0_map',
        'aligned exactly 1 time': 'stats_single_1_map',
        'aligned >1 times': 'stats_single_n_maps',
        'reads; of these:': 'stats_reads_count',
        'overall alignment rate': 'stats_map_rate'
    }

    def __init__(self) -> None:
        """
        Initialize Bowtie2
        :return: None
        """
        super(Bowtie2Map, self).__init__('bowtie2 map', '2.4.1')

        self._mod = None
        self._fastq_inputs_str = ''
        self._refgenome_str = ''
        self._readgroup_str = ''

    def _execute_tool(self) -> None:
        """
        Function to run Bowtie2 to map reads
        :return: None
        """
        self.__set_input()
        self.__set_output()
        self.__build_command()
        self._execute_command()
        self.__set_inform()

    def __set_input(self) -> None:
        """
        Set extra input
        :return: None
        """
        # Note that Bowtie2 can map both PE and SE reads together
        if 'FASTQ_PE' in self._tool_inputs:
            self._mod = 'PE'
            self._fastq_inputs_str += f" -1 {self._tool_inputs['FASTQ_PE'][0].path} " \
                                      f"-2 {self._tool_inputs['FASTQ_PE'][1].path}"
        if 'FASTQ_SE' in self._tool_inputs:
            if not self._mod:
                self._mod = 'SE'
            fq_input_str = ','.join(str(f.path) for f in self._tool_inputs['FASTQ_SE'])
            self._fastq_inputs_str += f' -U {fq_input_str}'

        self._refgenome_str = f"-x {self._tool_inputs['INDEX_GENOME_PREFIX'][0].value}"

        if 'SAMPLE_NAME' in self._tool_inputs:
            self._readgroup_str += f" --rg-id {self._tool_inputs['SAMPLE_NAME'][0].value}"
        elif 'read_group_id' in self._parameters:
            if self._parameters['read_group_id'].value == '':
                self._readgroup_str += f' --rg-id {Bowtie2Map.DEFAULT_SAMPLE_NAME}'
            else:
                self._readgroup_str += f" --rg-id {self._parameters['read_group_id'].value}"

    def _check_input(self) -> None:
        """
        Check input for Bowtie2 mapping
        :return: None
        """
        super()._check_input()
        if 'FASTQ_PE' in self._tool_inputs:
            if len(self._tool_inputs['FASTQ_PE']) != 2:
                raise ValueError("Paired end input requires exactly 2 files.")
        elif 'FASTQ_SE' not in self._tool_inputs:
            raise ValueError("No FASTQ_PE or FASTQ_SE input found")

        if 'INDEX_GENOME_PREFIX' not in self._tool_inputs:
            raise ValueError('No genome index input (INDEX_GENOME_PREFIX) found.')

    def __set_output(self) -> None:
        """
        Set output for Bowtie2 read mapping
        :return None
        """
        self._tool_outputs['SAM'] = [ToolIOFile(self.folder / Bowtie2Map.OUTPUT_NAME)]

    @staticmethod
    def __check_mode_exclusiveness(options: Set[str]) -> None:
        """
        Alignment mode exclusiveness check
        :param options: names of commandline options set
        """
        if ('end-to-end' in options) and ('local' in options):
            raise InvalidParameterError(
                "Bowtie2 reads mapping modes 'end-to-end' and 'local' are exclusive to each other, cannot be specified at the same time!"
            )

    @staticmethod
    def __check_presets_exclusiveness(align_mode: str, presets: List[str], options: Set[str]) -> None:
        """
        Check whether more than one preset is specified for a given alignment mode
        :param align_mode: current alignment mode
        :param presets: presets of current alignment mode
        :param options: names of commandline options set
        :return: None
        """
        p_count = 0
        for p in presets:
            if p in options:
                p_count += 1
        if p_count > 1:
            raise InvalidParameterError(
                f'Cannot set more than one preset for Bowtie2 mode {align_mode}, parameters set: {options}'
            )

    @staticmethod
    def __check_wrong_preset(align_mode: str, options: Set[str], wrong_presets: List[str]) -> None:
        """
        Check whether wrong preset is specified for a given alignment mode
        :param align_mode: current alignment mode
        :param options: names of commandline options set
        :param wrong_presets: presets should not be used with current alignment mode
        :return: None
        """
        for p in wrong_presets:
            # Note '-' is replaced with '_' for parameter name in db. Original name is used in here and the error
            # message for consistency and clarity.
            p_ = p.replace('-', '_')
            if p_ in options:
                raise InvalidParameterError(
                    f'Bowtie2 incompatible preset: reads mapping mode {align_mode}, preset {p}.')

    @staticmethod
    def __check_mode_preset_conflicts(options: Set[str]) -> None:
        """
        Alignment mode and preset conflicts check
        :param options: names of set options
        :return: None
        """
        local_preset = [
            'very-fast-local',
            'fast-local',
            'sensitive-local',
            'very-sensitive-local'
        ]
        end_to_end_preset = [
            'very-fast',
            'fast',
            'sensitive',
            'very-sensitive'
        ]
        if 'end-to-end' in options:
            Bowtie2Map.__check_wrong_preset('end-to-end', options, local_preset)
            Bowtie2Map.__check_presets_exclusiveness('end-to-end', end_to_end_preset, options)
        elif 'local' in options:
            Bowtie2Map.__check_wrong_preset('local', options, end_to_end_preset)
            Bowtie2Map.__check_presets_exclusiveness('local', local_preset, options)

    def _check_parameters(self) -> None:
        """
        Check the exclusiveness of different mods of Bowtie2 and the exclusiveness of presets for each mod and between mods
        :return: None
        """
        super(Bowtie2Map, self)._check_parameters()

        options = set(self._parameters.keys())
        Bowtie2Map.__check_mode_exclusiveness(options)
        Bowtie2Map.__check_mode_preset_conflicts(options)

    def __build_command(self, pipe_in: bool = False, pipe_out: bool = False) -> None:
        """
        Build command to run Bowtie2
        :return: None
        """
        if self._readgroup_str:
            command_parts = [
                self._tool_command,
                " ".join(self._build_options(excluded_parameters=['read_group_id'])),
                self._readgroup_str,
                self._refgenome_str,
                self._fastq_inputs_str
            ]
        else:
            command_parts = [
                self._tool_command,
                " ".join(self._build_options()),
                self._refgenome_str,
                self._fastq_inputs_str,
            ]
        if not pipe_out:
            command_parts.append(f"-S {self._tool_outputs['SAM'][0].path}")
        self._command = Command(' '.join(command_parts))

    def __set_time_inform(self, line: str) -> bool:
        """
        Set running time related information
        :param line: the content of current line (from self._command.stderr)
        :return: boolean, True if a time information is found
        """
        # time format: starts with number and composed of number and ":"
        res = re.search(r': (\d[\d|:]+)', line)
        if res:
            time = res.group().replace(": ", "")
            for pattern, key in Bowtie2Map.TIME_INFORM_MAPPING.items():
                if line.find(pattern) >= 0:
                    self.informs[key] = time
                    return True
        return False

    def __set_mapping_inform(self, line: str) -> None:
        """
        Set mapping result statistics information
        :param line: the content of current line (from self._command.stderr)
        :return: None
        """
        # search for all numbers
        res = re.findall(r'([\d|.]+)', line)
        if res:
            if line.find("pairs aligned 0 times concordantly or discordantly") > 0:
                # NOTE: this one also matches "aligned 0 times", but this is more specific, hence
                #       should be checked first
                self.informs['stats_pair_map_single'] = "{}".format(res[0])
                return

            for pattern, key in Bowtie2Map.ALIGN_INFORM_MAPPING.items():
                if line.find(pattern) > 0:
                    if len(res) > 1:
                        # two numbers found: count, percentage
                        self.informs[key] = f'{res[0]} ({res[1]}%)'
                    else:
                        # only one number found, count/percentage
                        self.informs[key] = f'{res[0]}'
                    return

    def __set_inform(self, stderr: Optional[str] = None) -> None:
        """
        Analyse the result of Bowtie2 reads mapping, and extra result statistics into tool inform.
        :param stderr: Command stderr (is taken from self._command when not specified)
        :return: None
        """
        self.informs['tool_name'] = 'Bowtie2'
        self.informs['mod'] = self._mod

        # parse output to extract information
        for line in (self.stderr if stderr is None else stderr).splitlines():
            time_inform_set = self.__set_time_inform(line)
            if not time_inform_set:
                self.__set_mapping_inform(line)

    def _before_pipe(self, dir_: Path, pipe_in: bool, pipe_out: bool) -> None:
        """
        Prepares the command that will be piped.
        :param dir_: Running directory
        :param pipe_in: True if tool receives piped input
        :param pipe_out: True if tool generates piped output
        :return: None
        """
        self.__set_input()
        self.__set_output()
        self.__build_command(pipe_in, pipe_out)

    def _after_pipe(self, stderr, is_last_in_pipe: bool) -> None:
        """
        Performs the required steps after executing the tool as part of a pipe.
        :param stderr: Stderr for this command in the pipe
        :param is_last_in_pipe: Boolean to indicate if this is the last step in the pipe
        :return: None
        """
        self.__set_inform(stderr)
