import logging
from typing import Dict, List, Union, Tuple, Any

from camel.app.components.files.fastautils import FastaUtils
from camel.app.components.statisticsutils import StatisticsUtils

from camel.app.error.invalidinputspecificationerror import InvalidInputSpecificationError
from camel.app.tools.tool import Tool


class SamtoolsDepthStatsAnalyzer(Tool):

    """
    Customized tool to analyze samtools depth output to extract read mapping statistics
    """
    def __init__(self) -> None:
        """
        Initializes this tool
        """
        super().__init__('samtools depth stats analyzer', '1.9')

    def _execute_tool(self) -> None:
        """
        Executes this tool
        :return: None
        """
        self.__analyze_depth_output()

    def _check_input(self) -> None:
        """
        Checks the input
        :return: None
        """
        if 'TXT' not in self._tool_inputs:
            raise InvalidInputSpecificationError("No samtools depth output TXT file file found as input.")
        if len(self._tool_inputs['TXT']) != 1:
            raise InvalidInputSpecificationError("Exactly one samtools depth output TXT file as input expected.")

        super(SamtoolsDepthStatsAnalyzer, self)._check_input()

    def __analyze_depth_output(self) -> None:
        """
        Analyze the depth output to gather various statistics
        :return: None
        """
        cov_cutoff = int(self._parameters['coverage_cutoff'].value) if ('coverage_cutoff' in self._parameters) else 0
        minimal_gap_len = int(self._parameters['minimal_gap_len'].value) if ('minimal_gap_len' in self._parameters) else 1

        refseq_length = {}
        if 'FASTA_REF' in self._tool_inputs:
            for ref_seq_id, seq in FastaUtils.read_as_dict(self._tool_inputs['FASTA_REF'][0].path).items():
                refseq_length[ref_seq_id] = len(seq)
            logging.debug('FASTA_REF refseq length: {}'.format(refseq_length))
            self.informs['refseq_length'] = refseq_length
        else:
            logging.warning(
                "No FASTA_REF input, reference sequence length unknown. An end gap will be reported for each covered reference sequence, and base coverage calculation skipped.")

        coverages, segment_coverages, segment_gaps, segment_base_count = SamtoolsDepthStatsAnalyzer.collect_inform(
            self._tool_inputs['TXT'][0].path, refseq_length, cov_cutoff, minimal_gap_len
        )

        if 'FASTA_REF' in self._tool_inputs:
            genome_base_coverage, segment_base_coverage = self.__calculate_base_coverage(
                segment_base_count, refseq_length)
        else:
            genome_base_coverage = 'NA'
            segment_base_coverage = {}
            for seq_id in segment_base_count:
                segment_base_coverage[seq_id] = 'NA'

        # whole genome statistics
        median = StatisticsUtils.median(coverages)
        self.informs['median_coverage'] = median
        self.informs['coverage_iqr'] = StatisticsUtils.interquartile(coverages)
        self.informs['coverage_cv'] = StatisticsUtils.cov(coverages)
        self.informs['coverage_mad'] = StatisticsUtils.mad(coverages, median)
        self.informs['coverage_std'] = StatisticsUtils.std(coverages)
        self.informs['base_coverage'] = genome_base_coverage

        # per sequence statistics
        self.informs['segment_base_count'] = segment_base_count
        self.informs['segment_gaps'] = segment_gaps
        self.informs['segment_median_coverage'] = {}
        self.informs['segment_coverage_mad'] = {}
        self.informs['segment_coverage_cv'] = {}
        self.informs['segment_coverage_iqr'] = {}
        self.informs['segment_coverage_std'] = {}
        self.informs['segment_base_coverage'] = {}
        for seq_id, seq_coverage in segment_coverages.items():
            median = StatisticsUtils.median(seq_coverage)
            self.informs['segment_median_coverage'][seq_id] = median
            self.informs['segment_coverage_mad'][seq_id] = StatisticsUtils.mad(seq_coverage, median)
            self.informs['segment_coverage_cv'][seq_id] = StatisticsUtils.cov(seq_coverage)
            self.informs['segment_coverage_iqr'][seq_id] = StatisticsUtils.interquartile(seq_coverage)
            self.informs['segment_coverage_std'][seq_id] = StatisticsUtils.std(seq_coverage)
            self.informs['segment_base_coverage'][seq_id] = segment_base_coverage[seq_id]

    @staticmethod
    def __calculate_base_coverage(segment_base_count, refseq_length) -> Tuple[int, Dict[Any, Union[float, str]]]:
        """
        Calculate the base coverage
        :param segment_base_count: base count per segment
        :param refseq_length: reference sequence length per segment
        :return: genome base coverage
        :return: per segment base coverage
        """
        genome_base_cov = None
        segment_base_cov = {}
        total_bases_covered = 0
        for seq_id in segment_base_count:
            total_bases_covered += segment_base_count[seq_id]
            if seq_id in refseq_length:
                segment_base_cov[seq_id] = 100.0 * segment_base_count[seq_id] / refseq_length[seq_id]
            else:
                logging.warning("Refseq {!r} length unknown, base coverage and genome coverage skipped.".format(seq_id))
                segment_base_cov[seq_id] = 'NA'
                genome_base_cov = 'NA'

        if genome_base_cov is None:
            genome_base_cov = 100.0 * sum(segment_base_count.values()) / float(sum(refseq_length.values()))

        return genome_base_cov, segment_base_cov

    @staticmethod
    def is_gap(cur_pos, last_pos, minimal_gap_len) -> bool:
        """
        Function to check whether there is a gap between current position and previous one
        :param cur_pos: current position reported
        :param last_pos: last position reported
        :param minimal_gap_len: minimal gap length, set a value > 0 to allow call gaps only with gaps of length larger then MINIMAL_GAP_LEN
        :return: True if a gap exist, False otherwise
        """
        return cur_pos - (last_pos + 1) >= minimal_gap_len

    @staticmethod
    def collect_inform(output_path, refseq_length, cov_cutoff=0, minimal_gap_len=1) -> Tuple[List[int], Dict[str, List[int]], Dict[str, list], Dict[str, int]]:
        """
        Collect coverage data from Samtools Depth output file, counting the bases covered, and discover gaps.
        :param output_path: Path to the output files
        :param cov_cutoff: coverage cutoff, only positions with coverage higher or equal to this cutoff are counted. Default 0.
        :param refseq_length: the dictionary contaning the length of genome segments
        :param minimal_gap_len: minimal gap length
        :return: coverages over complete genome
        :return: segment_coverages, coverage over each genome segment
        :return: segment_gaps, no coverage regions in a genome segment
        :return: segment_base_count, number of bases of a genome segment covered by reads
        """
        # Remark:
        # - samtools depth uses 1-based coordinate (1st base start at 1)
        # - gap: (start, end) closed definition, start and end inclusive. 1-based postion coordinate (1st base start at 1)
        # - when no gaps found for a segment, an empty list is initialized. This behavior is required for sequence extraction step later.
        #
        # Example output excerpt:
        #
        #    gi|407484675|ref|NC_018659.1|   88541   164
        #    gi|407484675|ref|NC_018659.1|   88542   161
        #    gi|407484675|ref|NC_018659.1|   88543   160
        #    gi|407484675|ref|NC_018659.1|   88544   157
        #    gi|407484773|ref|NC_018660.1|   4       1089
        #    gi|407484773|ref|NC_018660.1|   5       1115
        #    gi|407484773|ref|NC_018660.1|   6       1153
        #
        coverages = []
        segment_coverages = {}
        segment_base_count = {}
        segment_gaps = {}
        last_pos = 0
        last_seq_id = None
        with open(output_path) as output_file:
            for line in output_file:
                inform = line.split('\t')
                seq_id = inform[0]
                pos = int(inform[1])
                count = int(inform[2])
                # Note only position has coverage higher than cov_cutoff are counted
                if count > cov_cutoff:
                    coverages.append(count)
                    if seq_id == last_seq_id:
                        # Update the statistics for current sequence (seqid) and update gap if exists
                        segment_coverages[seq_id].append(count)
                        segment_base_count[seq_id] += 1
                        if SamtoolsDepthStatsAnalyzer.is_gap(pos, last_pos, minimal_gap_len):
                            segment_gaps[seq_id].append((last_pos + 1, pos - 1))

                    else:
                        # If a new sequence starts (see the output excerpt above), first update the last sequence with
                        # the possible tail gap, then initialize the statistics for the new sequence. Note that heading
                        # gap needs to be checked for the new sequence, as it is not guaranteed that the first base
                        # covered starts at base 1. (as shown in the example above)

                        if last_seq_id is not None:
                            SamtoolsDepthStatsAnalyzer.update_tail_gaps(
                                segment_gaps, last_seq_id, last_pos, refseq_length)

                        segment_coverages[seq_id] = [count]
                        segment_base_count[seq_id] = 1
                        segment_gaps[seq_id] = []
                        if SamtoolsDepthStatsAnalyzer.is_gap(pos, 0, minimal_gap_len):
                            segment_gaps[seq_id].append((1, pos - 1))

                    last_seq_id = seq_id
                    last_pos = pos

        # Handle the tail gap of the last sequence
        SamtoolsDepthStatsAnalyzer.update_tail_gaps(segment_gaps, last_seq_id, last_pos, refseq_length)

        return coverages, segment_coverages, segment_gaps, segment_base_count

    @staticmethod
    def update_tail_gaps(segment_gaps, seq_id, last_pos, refseq_length=None, minimal_gap_len=1) -> None:
        """
        Update segment_gaps with the tail gaps or a open gap if length is unknown
        :param segment_gaps: dictionary contain gaps of segments
        :param seq_id: sequence id of which the gaps will be updated
        :param last_pos: the last position which is covered by reads
        :param refseq_length: the dictionary containing the length of each reference sequence segment
        :param minimal_gap_len: minimal gap length
        :return: None
        """
        if refseq_length is None:
            refseq_length = {}
        last_gap = None
        if refseq_length:
            if seq_id in refseq_length:
                if refseq_length[seq_id] - last_pos > minimal_gap_len:
                    last_gap = (last_pos + 1, refseq_length[seq_id])

            else:
                logging.warning("Reference sequence with id {!r} is missing from FASTA_REF input.".format(seq_id))
                last_gap = (last_pos + 1, 'end')

        else:
            last_gap = (last_pos + 1, 'end')

        if last_gap:
            if seq_id in segment_gaps:
                segment_gaps[seq_id].append(last_gap)
            else:
                segment_gaps[seq_id] = [last_gap]
