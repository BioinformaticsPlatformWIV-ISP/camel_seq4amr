import logging
from pathlib import Path
from typing import List

from camel.app.error.invalidinputspecificationerror import InvalidInputSpecificationError
from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.io.tooliovalue import ToolIOValue
from camel.app.tools.tool import Tool
from camel.app.utils.blast.blasthitstatistics import BlastHitStatistics
from camel.app.utils.blasttyping.blasthitfilteringhelper import BlastHitFilteringHelper
from camel.app.utils.genedetection.genedetectionblasthit import GeneDetectionBlastHit


class BlastHitFiltering(Tool):
    """
    Class that filters blast hits and reports the best hits. Perfect hits are always reported. The best hits are
    selected from groups of overlapping hits.

    Input:
        TSV: Tabular file generated by Blastn with '7 pident sseqid sseq slen qseqid qstart qend' as output format.

    Output:
        VAL_Hits: A list with the detected hit objects.

    Important parameters:
    - extra_column_key & extra_column_name: If set, an extra metadata column is added to the detected hits. The key
      needs to match the key in the metadata dictionary.
    - filtering_method: Determines how the hits are filters. There are two options supported:
        * 'cluster' (default): The best hit for each cluster is reported.
        * 'score': The n best hits according to hit score are reported (controlled by the 'score_limit' parameter).
    """

    def __init__(self) -> None:
        """
        Initializes this tool.
        """
        super().__init__('Gene Detection: Hit Filtering', '0.1')

    def _execute_tool(self) -> None:
        """
        Executes this tool.
        :return: None
        """
        hits = self.__parse_tabular_blast_output(self._tool_inputs['TSV'][0].path)
        filtered_hits = self.__filter_hits(hits)
        self._tool_outputs['VAL_Hits'] = [ToolIOValue(hit) for hit in filtered_hits]
        self.__set_informs()

    def _check_input(self) -> None:
        """
        Checks whether the input is correct.
        :return: None
        """
        if 'TSV' not in self._tool_inputs:
            raise InvalidInputSpecificationError("No 'TSV' input found.")
        super(BlastHitFiltering, self)._check_input()

    def __parse_tabular_blast_output(self, tsv_file: Path) -> List[GeneDetectionBlastHit]:
        """
        Parses the tabular input file.
        :param tsv_file: TSV input file
        :return: Parsed BLAST hits per cluster
        """
        hits = []
        for stats in BlastHitStatistics.parse_blast_output(tsv_file):
            seq_id = stats.subject_id.split('__')[2]
            hits.append(GeneDetectionBlastHit(seq_id, None, stats))
        logging.info(f"{len(hits)} hits parsed")
        return hits

    def __filter_hits(self, hits: List[GeneDetectionBlastHit]) -> List[GeneDetectionBlastHit]:
        """
        Filters hits based on the given tool parameters.
        :param hits: Input BLAST hits
        :return: List of filtered BLAST hits
        """
        hits = BlastHitFilteringHelper.filter_percent_identity(hits, float(
            self._parameters['min_percent_identity'].value))
        hits = BlastHitFilteringHelper.filter_coverage(hits, float(self._parameters['min_coverage'].value))
        logging.info("Filtering method: '{}'".format(self._parameters['filtering_method'].value))

        # Report best hit(s) for each database cluster
        if self._parameters['filtering_method'].value == 'cluster':
            hits = BlastHitFiltering.__get_best_hit_per_cluster(hits)
            hits.sort(key=lambda h: (h.locus, h.blast_stats.query_start))

        # Report best N hits based on BLAST score
        elif self._parameters['filtering_method'].value == 'score':
            if 'score_nb_of_hits' not in self._parameters:
                raise ToolExecutionError("'score_nb_of_hits' needs to be set when the filtering method is 'score'")
            hits = hits[:int(self._parameters['score_nb_of_hits'].value)]
        return hits

    @staticmethod
    def __get_best_hit_per_cluster(hits: List[GeneDetectionBlastHit]) -> List[GeneDetectionBlastHit]:
        """
        Returns the best hit for each cluster.
        :param hits: All hits
        :return: Best matching hits
        """
        hits_per_cluster = {}
        for hit in hits:
            cluster = hit.blast_stats.subject_id.split('__')[1]
            if cluster not in hits_per_cluster:
                hits_per_cluster[cluster] = []
            hits_per_cluster[cluster].append(hit)
        logging.debug('{} cluster(s) with hits'.format(len(hits_per_cluster)))

        reported_hits = []
        for _, hits in hits_per_cluster.items():
            selected_hits = BlastHitFilteringHelper.detect_best_hits(hits)
            reported_hits.extend(selected_hits)
        return reported_hits

    def __set_informs(self) -> None:
        """
        Sets the informs.
        :return: None
        """
        self._informs['Min. percent identity'] = f"{self._parameters['min_percent_identity'].value}%"
        self._informs['Min. coverage'] = f"{self._parameters['min_coverage'].value}%"