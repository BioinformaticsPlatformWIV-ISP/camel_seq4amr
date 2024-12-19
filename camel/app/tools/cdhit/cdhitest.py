from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import re

from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.tool import Tool
from camel.app.utils.command import Command


@dataclass
class Cluster:
    """
    This class represents a group of sequences that cluster together.
    """
    name: str
    number: int
    seq_ids: List[str] = field(default_factory=list)


class CDHitEst(Tool):
    """
    CD-HIT is a program used for clustering and comparing protein or nucleotide sequences.
    """

    def __init__(self) -> None:
        """
        Initializes this tool.
        """
        super().__init__('cd-hit-est')

    def _execute_tool(self) -> None:
        """
        Executes this tool.
        :return: None
        """
        output_path = self.folder / 'out.fasta'
        self.__build_command(output_path)
        self._execute_command()
        self._tool_outputs['FASTA'] = [ToolIOFile(output_path)]
        self._informs['clusters'] = CDHitEst.__parse_clusters(output_path.parent / f'{output_path.name}.clstr')

    def __build_command(self, output_path: Path) -> None:
        """
        Builds the command line call.
        :param output_path: Output file path
        :return: None
        """
        self._command.command = ' '.join([
            self._tool_command,
            f"-i {self._tool_inputs['FASTA'][0].path}",
            f"-o {output_path}",
            '-d 0'] + self._build_options()
        )

    @staticmethod
    def __parse_clusters(path: Path) -> List[Cluster]:
        """
        Parses a FASTA file and returns the clusters.
        :param path: Path to the clusters output file.
        :return: A list of clusters
        """
        clusters = []
        with path.open() as handle:
            for line in handle.readlines():
                if line.startswith('>'):
                    name = line.strip()[1:].replace(' ', '_')
                    clusters.append(Cluster(name, int(name.split('_')[-1])))
                else:
                    clusters[-1].seq_ids.append(CDHitEst.__parse_cluster_line(line.strip()))
        return clusters

    @staticmethod
    def __parse_cluster_line(line: str) -> str:
        """
        Parses a cluster line and returns the sequence name.
        :param line: Input line
        :return: Sequence name
        """
        match = re.match('\\d.+, >(seq_\\d+)\\.{3}.*', line)
        if not match:
            raise ValueError(f'Invalid cluster line: {line}')
        return match.group(1)

    def get_version(self) -> str:
        """
        Returns the version of the tool.
        :return: Tool version
        """
        command = Command(f'{self._tool_command} -h')
        command.run(Path().cwd(), disable_logging=True)
        return re.search(f'CD-HIT version (.*) \(built on', command.stdout).group(1).strip()
