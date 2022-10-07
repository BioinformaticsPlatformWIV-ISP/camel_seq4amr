import datetime
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import humanize
from Bio import SeqIO

from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.blast.makeblastdb import MakeBlastDb
from camel.app.tools.bowtie2.bowtie2index import Bowtie2Index
from camel.app.tools.cdhit.cdhitest import CDHitEst, Cluster
from camel.app.tools.kma.kma import KMA
from camel.app.tools.samtools.samtoolsfastaindex import SamtoolsFastaIndex
from camel.app.utils.command import Command


class DBHelper(object):
    """
    This helper class is used to construct gene detection databases.
    """

    def __init__(self, db_name: str, working_dir: Path) -> None:
        """
        Initializes the update helper.
        :param db_name: Database name
        :param working_dir: Working directory
        """
        self._db_name = db_name
        self._working_dir = working_dir
        self._informs = []

    @property
    def informs(self) -> List[Dict[str, Any]]:
        """
        Returns the informs.
        :return: Informs
        """
        return self._informs

    def get_working_subdir(self, name: str) -> Path:
        """
        Returns the path to the given sub directory.
        The directory is created if it does not exist yet.
        :param name: Directory name
        :return: Path
        """
        path = self._working_dir / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_clusters_form_fasta(self, fasta_file: Path, clustering_cutoff: float) -> List[Cluster]:
        """
        Returns the clusters of similar sequences from the given FASTA file.
        :param fasta_file: Input FASTA file
        :param clustering_cutoff: Clustering cutoff (0.0 - 1.0)
        :return: List of clusters
        """
        cdhit = CDHitEst()
        cdhit.update_parameters(identitiy_threshold=str(clustering_cutoff / 100))
        cdhit.add_input_files({'FASTA': [ToolIOFile(fasta_file)]})
        cdhit.run(self.get_working_subdir('clustering'))
        self._informs.append(cdhit.informs)
        return cdhit.informs['clusters']

    def index_samtools_faidx(self, fasta_file: Path, working_dir: Path) -> None:
        """
        Indexes the given FASTA file with samtools faidx.
        :param fasta_file: Input FASTA file
        :param working_dir: Working directory
        :return: None
        """
        samtools_faindex = SamtoolsFastaIndex()
        samtools_faindex.add_input_files({'FASTA': [ToolIOFile(fasta_file)]})
        samtools_faindex.run(working_dir)
        self._informs.append(samtools_faindex.informs)

    def index_bowtie2(self, fasta_file: Path, working_dir: Path) -> None:
        """
        Creates a bowtie2 index for the given FASTA file.
        :param fasta_file: Input FASTA file
        :param working_dir: Working directory
        :return: None
        """
        bowtie2_index = Bowtie2Index()
        bowtie2_index.add_input_files({'FASTA_REF': [ToolIOFile(fasta_file)]})
        bowtie2_index.run(working_dir)
        self._informs.append(bowtie2_index.informs)

    def index_blast(self, fasta_file: Path, working_dir: Path) -> None:
        """
        Indexes the given FASTA file with makeblastdb.
        :param fasta_file: Input FASTA file
        :param working_dir: Working directory
        :return: None
        """
        makeblastdb = MakeBlastDb()
        makeblastdb.add_input_files({'FASTA': [ToolIOFile(fasta_file)]})
        makeblastdb.run(working_dir)
        self._informs.append(makeblastdb.informs)

    def index_kma(self, fasta_file: Path, working_dir: Path) -> None:
        """
        Creates a KMA index.
        :param fasta_file: FASTA file
        :param working_dir: Working directory
        :return: None
        """
        logging.info(f'Indexing - KMA: {fasta_file}')
        kma = KMA()
        path_out = fasta_file.parent / 'kma' / fasta_file.stem
        if not path_out.parent.exists():
            path_out.parent.mkdir(parents=True)
        command = Command(
            f"ml {' '.join(kma.dependencies)}; kma index -i {fasta_file} -o {path_out}")
        command.run(working_dir)
        if command.returncode != 0:
            raise RuntimeError(f"Error KMA indexing: {command.stderr}")
        self._informs.append({'_command': command.command, '_name': 'KMA', '_version': kma.version})

    def convert_fasta_headers_to_seq(self, input_file: Path, output_file: Path) -> Dict[str, str]:
        """
        Creates a fasta file where all ids are replaced by seq_{number}.
        This ensures that CD-HIT can work properly.
        :param input_file: Input FASTA file
        :param output_file: Output FASTA file
        :return: Mapping of original headers to novel headers
        """
        seq_ids = {}
        output_seqs = []
        with input_file.open() as handle_in:
            for seq in SeqIO.parse(handle_in, 'fasta'):
                new_name = 'seq_{}'.format(len(seq_ids))
                seq_ids[new_name] = seq.description
                seq.id = new_name
                seq.description = ''
                output_seqs.append(seq)
        with output_file.open('w') as handle_out:
            SeqIO.write(output_seqs, handle_out, 'fasta')
        return seq_ids

    @staticmethod
    def create_srst2_fasta(input_fasta: Path, output_fasta: Path, clusters: List[Cluster]) -> None:
        """
        Creates a FASTA file compatible with SRST2.
        The format is: >[clusterUniqueIdentifier]__[clusterSymbol]__[alleleSymbol]__[alleleUniqueIdentifier]
        :param input_fasta: FASTA containing the renamed sequences
        :param output_fasta: Output FASTA file
        :param clusters: Sequence clusters
        :return: Path to generated FASTA file
        """
        seq_record_by_id = {}
        with input_fasta.open() as handle_in:
            for seq in SeqIO.parse(handle_in, 'fasta'):
                seq_record_by_id[seq.id] = seq
                seq.description = ''

        output_seqs = []
        for i, cluster in enumerate(clusters):
            for sequence_name in cluster.seq_ids:
                seq = seq_record_by_id[sequence_name]
                full_name = seq.id
                seq.id = '__'.join([str(i), cluster.name, full_name, full_name])
                output_seqs.append(seq)

        with output_fasta.open('w') as handle_out:
            SeqIO.write(output_seqs, handle_out, 'fasta')

    def export_metadata(self, name: str, dir_output: Path) -> None:
        """
        Exports the database metadata.
        :param name: Database name
        :param dir_output: Output directory
        :return: None
        """
        metadata_file = dir_output / 'db_metadata.txt'
        logging.info(f'Exporting metadata: {metadata_file}')
        metadata = {'name': name.lower(), 'title': name, 'last_updated': datetime.date.today().strftime("%d-%m-%Y")}
        with metadata_file.open('w') as handle:
            json.dump(metadata, handle, indent=4, sort_keys=True)
        logging.info(f"Metadata exported: {metadata_file}")

    def standardize_fasta_headers(self, input_fasta: Path) -> Path:
        """
        Reformat the headers of the input FASTA file.
        :param input_fasta: Input FASTA file
        :return: Reformatted FASTA file
        """
        dir_reformat = self._working_dir / 'reformat'
        if not dir_reformat.exists():
            dir_reformat.mkdir()
        output_path = dir_reformat / f'{Path(input_fasta).stem.lower()}.fasta'
        with input_fasta.open() as handle:
            seqs = list(SeqIO.parse(handle, 'fasta'))
        for s in seqs:
            data = {'allele': s.id}
            s.description = json.dumps(data)
        with output_path.open('w') as handle:
            SeqIO.write(seqs, handle, 'fasta')
        logging.info(
            f"Reformatted FASTA file created ({humanize.naturalsize(output_path.stat().st_size)}): {output_path}")
        return output_path

    def export_mapping(self, mapping: Dict[str, str], clusters: List[Cluster], output_directory: Path) -> None:
        """
        Exports the mapping of the novel headers to the original headers.
        :param mapping: Mapping
        :param clusters: Clusters
        :param output_directory: Output directory
        :return: None
        """
        with (output_directory / 'mapping.txt').open('w') as handle:
            json.dump(mapping, handle, indent=4, sort_keys=True)
        logging.info(f"Metadata exported: {output_directory}")

        cluster_by_seq_id = {}
        for c in clusters:
            for seq_id in c.seq_ids:
                cluster_by_seq_id[seq_id] = c.name

        seq_metadata = {}
        for seq_id, full_header in mapping.items():
            parts = full_header.split(' ')
            seq_data = json.loads(' '.join(parts[1:]))
            seq_data['header_orig'] = parts[0]
            try:
                seq_data['cluster'] = cluster_by_seq_id[seq_id]
            except KeyError:
                continue
            seq_metadata[seq_id] = seq_data
        with (output_directory / 'mapping_full.json').open('w') as handle:
            json.dump(seq_metadata, handle, indent=2)
