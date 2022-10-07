import logging
from typing import List, Union

from camel.app.utils.genedetection.genedetectionblasthit import GeneDetectionBlastHit


class BlastHitFilteringHelper(object):
    """
    Class that filters list of BlastHit objects.
    """

    BlastHit = Union[GeneDetectionBlastHit]

    @staticmethod
    def detect_best_hits(hits: List[BlastHit]) -> List[BlastHit]:
        """
        Detects the best hits out of a list of BLAST hits.
        Cases:
        - If a perfect hit is found the perfect hit is returned.
        - If multiple perfect hits are found, the longest one is returned.
        - If no perfect hit is detected, the best imperfect hit is returned.
        - If there are multiple equivalent best imperfect hits, all of them are returned.
        :param hits: Hits
        :return: Best hit(s)
        """
        logging.debug("Detecting best from list of {} hit(s)".format(len(hits)))
        if len(hits) == 0:
            raise ValueError("Input list is empty")
        perfect_hits = [h for h in hits if h.blast_stats.is_perfect_hit()]
        if len(perfect_hits) >= 1:
            logging.debug('{} perfect hit(s) found: {}'.format(
                len(perfect_hits), ', '.join([h.locus for h in perfect_hits])))
            max_length = max([h.blast_stats.subject_length for h in perfect_hits])
            return [h for h in perfect_hits if h.blast_stats.subject_length == max_length]
        else:
            best_hits = BlastHitFilteringHelper.__get_best_imperfect_hits(hits)
            logging.debug('No perfect hits found, {} equivalent imperfect hits found: {}'.format(
                len(best_hits), ', '.join([h.locus for h in best_hits])))
            return best_hits

    @staticmethod
    def __get_best_imperfect_hits(hits: List[BlastHit]) -> List[BlastHit]:
        """
        Returns the best imperfect hits from a list of blast hits. If there are multiple equivalent imperfect hits,
        all of them are returned.
        :param hits: List of hits
        :return: Best hit
        """
        lowest_length_score = min([BlastHitFilteringHelper.__calculate_length_score(hit) for hit in hits])
        lowest_ls_hits = [hit for hit in hits if
                          BlastHitFilteringHelper.__calculate_length_score(hit) == lowest_length_score]

        highest_pident = max([hit.blast_stats.percent_identity for hit in lowest_ls_hits])
        highest_pident_hits = [hit for hit in lowest_ls_hits if hit.blast_stats.percent_identity == highest_pident]

        longest_alignment = max([hit.blast_stats.alignment_length for hit in highest_pident_hits])
        longest_alignment_hits = [
            hit for hit in highest_pident_hits if hit.blast_stats.alignment_length == longest_alignment]

        return longest_alignment_hits

    @staticmethod
    def __calculate_length_score(hit: BlastHit) -> int:
        """
        Calculates the length score for a Blast hit.
        The score is calculated as described in: https://www.ncbi.nlm.nih.gov/pubmed/22238442

        The best-matching MLST allele is found by calculating the length score (LS) as QL - HL + G, where QL is the
        length of the MLST allele, HL is the length of the HSP, andGis the number of gaps in the HSP. The allele with
        the lowest LS and, secondly, with the highest percentage of identity (ID) is selected as the best-matching MLST
        allele.
        :param hit: Blast hit
        :return: Length score
        """
        return hit.blast_stats.subject_length - hit.blast_stats.alignment_length + hit.blast_stats.gaps

    @staticmethod
    def filter_percent_identity(hits: List[BlastHit], min_percent_identity: float) -> List[BlastHit]:
        """
        Filters a list of BLAST hits based on percent identity.
        :param hits: List of BLAST hits
        :param min_percent_identity: Minimal percent identity
        :return: Filtered hits
        """
        filtered_hits = [hit for hit in hits if hit.blast_stats.percent_identity >= min_percent_identity]
        logging.info('{}/{} hits passed percent identity filtering ({} %)'.format(
            len(filtered_hits), len(hits), min_percent_identity))
        return filtered_hits

    @staticmethod
    def filter_coverage(hits: List[BlastHit], min_coverage: float) -> List[BlastHit]:
        """
        Filters a list of BLAST hits based on coverage.
        :param hits: List of BLAST hits
        :param min_coverage: Minimal coverage
        :return: Filtered hits
        """
        filtered_hits = [hit for hit in hits if hit.blast_stats.subject_coverage >= min_coverage]
        logging.info('{}/{} hits passed length coverage filtering ({} %)'.format(
            len(filtered_hits), len(hits), min_coverage))
        return filtered_hits
