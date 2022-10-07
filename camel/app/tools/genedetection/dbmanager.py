import json
from pathlib import Path

from camel.app.error.invalidinputspecificationerror import InvalidInputSpecificationError
from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.io.tooliodirectory import ToolIODirectory
from camel.app.io.tooliofile import ToolIOFile
from camel.app.tools.tool import Tool
from camel.app.utils.genedetection.mapping import Mapping


class DBManager(Tool):
    """
    Tool that manages gene databases.

    INPUT:
    - DIR: Directory containing an indexed FASTA file and a last_update file containing the date of the last database
        update.

    OUTPUT:
    - FASTA: FASTA file from the input directory
    - FASTA_clustered: Clustered FASTA file

    INFORMS:
    - title: Database title
    - name: Database name
    - last_updated: Date of the last database update
    - clustering_cutoff: Clustering cutoff of the database
    - mapping: Mapping of converted sequence names to original headers
    """

    def __init__(self) -> None:
        """
        Initialize this tool.
        :return: None
        """
        super().__init__('Gene Detection: DB Manager', '0.1')

    def _execute_tool(self) -> None:
        """
        Runs this tool.
        :return: None
        """
        input_folder = self._tool_inputs['DIR'][0].path
        self.__set_database_files(input_folder)
        self.__add_informs(input_folder)

    def _check_input(self) -> None:
        """
        Checks whether the input is correct.
        :return: None
        """
        if 'DIR' not in self._tool_inputs:
            raise InvalidInputSpecificationError("No 'DIR' input found.")
        if not isinstance(self._tool_inputs['DIR'][0], ToolIODirectory):
            raise InvalidInputSpecificationError("'{}' is not a directory".format(self._tool_inputs['DIR'][0]))
        super(DBManager, self)._check_input()

    def __add_informs(self, input_folder: Path) -> None:
        """
        Adds the informs by parsing the JSON file containing the metadata in the database directory.
        :param input_folder: Input database directory
        :return: None
        """
        path_metadata = input_folder / 'db_metadata.txt'
        if not path_metadata.is_file():
            raise FileNotFoundError(f'Database metadata not found: {path_metadata}')
        with path_metadata.open() as handle:
            metadata = json.load(handle)
        self._informs.update(metadata)
        self._informs['mapping'] = self.__get_mapping(input_folder)

    @staticmethod
    def __get_mapping(input_folder: Path) -> Mapping:
        """
        Returns the mapping of the standardized header to the original header.
        :param input_folder: Input folder
        :return: Header mapping
        """
        try:
            return Mapping.parse((input_folder / 'mapping.txt'))
        except FileNotFoundError:
            raise ToolExecutionError(f'No mapping found in {input_folder}')

    def __set_database_files(self, folder: Path) -> None:
        """
        Returns the FASTA file from the given folder.
        :return: Database file
        """
        for f in folder.iterdir():
            if f.name.endswith('.fasta') and ('clustered' in f.name):
                self._tool_outputs['FASTA_clustered'] = [ToolIOFile(f)]
            elif f.name.endswith('.fasta'):
                self._tool_outputs['FASTA'] = [ToolIOFile(f)]
