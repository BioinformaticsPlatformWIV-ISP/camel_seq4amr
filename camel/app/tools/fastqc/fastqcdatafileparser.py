import logging
from pathlib import Path
from typing import Dict, List

from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.tool import Tool


class FastQCDataFileParser(Tool):
    """
    Class that performs various quality checks based on FastQC output.
    """

    def __init__(self) -> None:
        """
        Initialize this tool.
        """
        super().__init__('FastQC additional checks', '0.1')

    def _check_input(self) -> None:
        """
        Checks whether all the required input files are in the inputs.
        :return: None
        """
        if 'TXT' not in self._tool_inputs:
            raise ValueError("No TXT input found.")
        super(FastQCDataFileParser, self)._check_input()

    def _execute_tool(self) -> None:
        """
        Performs the quality checks.
        :return: None
        """
        self._informs['stats'] = {
            'mode_read_length_raw': self._get_mode_read_length(self._tool_inputs['TXT_RAW'][0].path),
        }
        self._informs['by_file'] = {k: [] for k in [
            'nb_reads', 'avg_read_qual', 'gc_content', 'max_n_frac', 'qscore_drop_pos', 'max_per_base_diff',
            'median_seq_len']}
        self._informs['params'] = {}

        for fastqc_txt in self._tool_inputs['TXT']:
            # Parse modules
            module_by_name = self.__split_modules(fastqc_txt)

            # Total reads
            total_nb_reads = self.__get_total_reads(module_by_name['Basic Statistics'])
            self._informs['by_file']['nb_reads'].append(total_nb_reads)

            # Avg. read quality
            self._informs['by_file']['avg_read_qual'].append(FastQCDataFileParser.__get_average_read_quality(
                module_by_name['Per sequence quality scores']))

            # GC-content
            self._informs['by_file']['gc_content'].append(FastQCDataFileParser.__get_gc_content(
                module_by_name['Basic Statistics']))

            # N-fraction
            self._informs['by_file']['max_n_frac'].append(FastQCDataFileParser.__get_max_n_fraction(
                module_by_name['Per base N content']))

            # Q-score drop
            threshold = float(self._parameters['qscore_drop_threshold'].value)
            self._informs['params']['qscore_drop_pos'] = {'threshold': threshold}
            self._informs['by_file']['qscore_drop_pos'].append(FastQCDataFileParser.__get_mean_qscore_drop(
                module_by_name['Per base sequence quality'], threshold))

            # Per-base sequence content
            skipped_start = int(self._parameters['per_base_sequence_content_skipped'].value)
            skipped_end = int(self._parameters['per_base_sequence_content_skipped_end'].value)
            self._informs['params']['per_b_seq_content'] = {'skipped_start': skipped_start, 'skipped_end': skipped_end}
            self._informs['by_file']['max_per_base_diff'].append(FastQCDataFileParser.__get_max_seq_content_diff(
                module_by_name['Per base sequence content'], skipped_start, skipped_end))

            # Sequence length distribution
            self._informs['by_file']['median_seq_len'].append(FastQCDataFileParser.__get_median_read_length(
                module_by_name['Sequence Length Distribution'], total_nb_reads))

    @staticmethod
    def __split_modules(input_file: ToolIOFile) -> Dict[str, List[str]]:
        """
        Get the content of the different modules of the fastqc data file.
        :param input_file: Name of the fastqc data file
        :return: Modules with the content
        """
        modules = {}
        with input_file.path.open() as file_:
            key = None
            content = []
            for line in file_.readlines():
                if line.strip() == '>>END_MODULE':
                    modules[key] = content
                    content = []
                elif line.startswith('>>'):
                    key = line[2:].strip().split('\t')[0]
                else:
                    content.append(line.strip())
        return modules

    @staticmethod
    def __get_total_reads(data: List[str]) -> int:
        """
        Returns the total number of reads.
        :param data: Module data
        :return: Total nb of reads
        """
        for line in data:
            if not line.startswith('Total Sequences'):
                continue
            return int(line.split('\t')[1])
        raise ValueError("Cannot find total number of reads in FastQC data file")

    @staticmethod
    def __get_average_read_quality(data: List[str]) -> float:
        """
        Returns the average read quality.
        :param data: Per sequence quality scores data
        :return: Average read quality
        """
        total_count = 0.0
        total_quality = 0.0
        for row in data[1:]:
            quality, count = row.split('\t')
            total_count += float(count)
            total_quality += float(quality) * float(count)
        return total_quality / total_count

    @staticmethod
    def __get_max_n_fraction(data: List[str]) -> float:
        """
        Returns the maximum N fraction.
        Note: FastQC reports in % per position so to obtain fraction it is divided by 100.
        :param data: Per base N content data
        :return: Fraction
        """
        max_percentage = 0.0
        for row in data[1:]:
            base, n_percentage = row.split('\t')
            if float(n_percentage) > max_percentage:
                max_percentage = float(n_percentage)
        return max_percentage / 100

    @staticmethod
    def __get_gc_content(data: List[str]) -> float:
        """
        Returns the GC content.
        :param data: Basic statistics data
        :return: GC content
        """
        for line in data:
            if line.startswith('%GC'):
                return float(line.split('\t')[1])
        raise ValueError('GC content not found in FastQC data file')

    @staticmethod
    def _get_mode_read_length(data_file: Path) -> int:
        """
        Returns the median read length as reported by FastQC.
        :param data_file: Data file
        :return: Median read length
        """
        target_lines = []
        keep = False
        with data_file.open() as handle:
            for line in handle.readlines():
                if keep is True:
                    if line.startswith('>>END_MODULE'):
                        break
                    else:
                        target_lines.append(line.strip())
                if line.startswith('>>Sequence Length Distribution'):
                    keep = True

        max_count = 0
        mode = 0
        for line in target_lines[1:]:
            parts = line.split('\t')
            count = float(parts[-1])
            if count > max_count:
                max_count = count
                interval_median = sum([int(x) for x in parts[0].split('-')]) / 2 if '-' in parts[0] else int(parts[0])
                mode = int(interval_median)
        return mode

    @staticmethod
    def __get_mid_point(interval_str: str) -> int:
        """
        Gets the mid point of an interval in the FastQC output.
        :param interval_str: Interval string
        :return: Mid point
        """
        if '-' in interval_str:
            return sum([int(x) for x in interval_str.split('-')]) // 2
        else:
            return int(interval_str)

    @staticmethod
    def __get_median_read_length(data: List[str], total_nb_reads: int) -> int:
        """
        Returns the (estimated) median read length.
        :param data: Data
        :param total_nb_reads: Total number of reads
        :return: Median read length
        """
        reads_counted = 0
        for length, count in [line.split('\t') for line in data[1:]]:
            reads_counted += float(count)
            if reads_counted > total_nb_reads / 2:
                return FastQCDataFileParser.__get_mid_point(length)
        raise ValueError("Invalid total number of reads")

    @staticmethod
    def __get_mean_qscore_drop(data: List[str], threshold: float) -> float:
        """
        Returns the base where the mean qscore drops below the threshold.
        :param data: Per base sequence quality data
        :param threshold: Threshold
        :return: base
        """
        for row in data[1:]:
            base = row.split('\t')[0]
            mean_q_score = row.split('\t')[1]
            if float(mean_q_score) < threshold:
                return float(base.split('-')[0])
        return float('inf')

    @staticmethod
    def __get_max_seq_content_diff(data: List[str], nb_of_skipped_bases: int, nb_of_skipped_bases_end: int) -> float:
        """
        Returns the maximal difference between A-T and C-G.
        :param data: Per base sequence content data
        :param nb_of_skipped_bases: Nb of bases to skip in the start of the reads
        :param nb_of_skipped_bases: Nb of bases to skip at the end of the reads
        :return: Difference
        """
        max_difference = 0.0
        last_base = int(data[-1].split('\t')[0].split('-')[-1])
        logging.debug("Checking A-T, G-C difference between base {} and {}".format(
            nb_of_skipped_bases, last_base - nb_of_skipped_bases_end))
        for row in data[1:]:
            base, freq_g, freq_a, freq_t, freq_c = row.split('\t')
            interval_upper = int(base.split('-')[-1])
            if nb_of_skipped_bases < interval_upper <= (last_base - nb_of_skipped_bases_end):
                at_difference = abs(float(freq_a) - float(freq_t))
                if at_difference > max_difference:
                    max_difference = at_difference
                gc_difference = abs(float(freq_c) - float(freq_g))
                if gc_difference > max_difference:
                    max_difference = gc_difference
        return max_difference
