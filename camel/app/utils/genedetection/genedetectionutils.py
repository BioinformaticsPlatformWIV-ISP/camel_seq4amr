import ast
import json
import logging
from typing import Tuple, Dict, List

import bs4
import re
from Bio import SeqIO


class GeneDetectionUtils(object):
    """
    This class contains utility functions for the gene detection workflow.
    """

    @staticmethod
    def parse_header(header: str) -> Tuple[str, Dict]:
        """
        Parses a gene detection header. The format is:
        >{sequence id} {metadata in JSON format}
        :param header: Complete header
        :return: sequence id, metadata
        """
        m = re.match('^(.*) ({.*})$', header)
        if not m:
            raise ValueError("Invalid header: {}".format(header))
        metadata = json.loads(m.group(2))
        return m.group(1), metadata

    @staticmethod
    def is_ncbi_accession(accession: str) -> bool:
        """
        Checks whether the given accession is a NCBI accession.
        :param accession: Accession
        :return: True if it is a NCBI accession
        """
        m = re.match(r'\w{1,4}[\d.]+', accession)
        if m:
            return True
        return False

    @staticmethod
    def extract_report_section_content(html_code: str, include_header=False) -> str:
        """
        Extracts the content of the gene detection output report section.
        :param html_code: HTML code of the output section
        :param include_header: If True, header is included
        :return: Extracted content
        """
        content = bs4.BeautifulSoup(html_code, 'html.parser')
        parts = []
        for x in content.find('div').contents:
            if (include_header is False) and (x.name == 'h3'):
                continue
            parts.append(str(x))
        return "".join(parts)

    @staticmethod
    def get_detection_method_key(config: Dict, db_key: str) -> str:
        """
        Returns the database path for the given database based on the configuration.
        :param config: Snakemake configuration
        :param db_key: Database key
        :return: Detection method key
        """
        try:
            db_config = config['gene_detection'][db_key]
        except KeyError:
            raise ValueError(f"Database '{db_key}' not found in Snakemake config")
        return db_config.get('force_detection_method', config['detection_method'])

    @staticmethod
    def parse_extra_column_param(value: str) -> Tuple[str, str]:
        """
        Parses the value of the extra column parameter.
        :return: Column name, column id
        """
        try:
            name, key = ast.literal_eval(value)
            return name, key
        except SyntaxError:
            raise ValueError(f"Badly formatted parameter value: {value}")

    @staticmethod
    def parse_clusters(clustered_fasta: str) -> Dict[str, str]:
        """
        Parses the clusters from a clustered gene detection FASTA file.
        :param clustered_fasta: Clustered FASTA file
        :return: Mapping of seq_NN to cluster
        """
        cluster_by_seq = {}
        with open(clustered_fasta) as handle:
            for seq in SeqIO.parse(handle, 'fasta'):
                parts = seq.id.split('__')
                cluster_by_seq[parts[2]] = parts[1]
        unique_clusters = set(cluster_by_seq.values())
        logging.info(f"Clustering mapping parsed for {len(cluster_by_seq)} sequences ({len(unique_clusters)} "
                     f"unique clusters)")
        return cluster_by_seq

    @staticmethod
    def export_hits_tabular(hits: List, output_path: str) -> None:
        """
        Creates the tabular output file.
        :param hits: Detected hits
        :param output_path: Output path
        :return: None
        """
        logging.info(f"Exporting {len(hits)} hits to: {output_path}")
        with open(output_path, 'w') as handle:
            if len(hits) < 1:
                return
            handle.write('\t'.join(hits[0].table_column_names))
            handle.write('\n')
            for hit in hits:
                handle.write('\t'.join(hit.to_table_row()))
                handle.write('\n')
