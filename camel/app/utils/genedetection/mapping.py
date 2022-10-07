from pathlib import Path
from typing import Dict, Optional

import json


class Mapping(object):
    """
    This class contains a mapping of the converted sequence name to the original header.
    The main purpose of this class is to avoid cluttering of the log with the complete mapping as a dictionary.
    """

    def __init__(self, content: Dict[str, str]):
        """
        Initializes a mapping.
        :param content: Mapping content
        """
        self._content = content

    @staticmethod
    def parse(input_file: Path) -> 'Mapping':
        """
        Parses a mapping from a file.
        :param input_file: Input file
        :return: Mapping
        """
        with input_file.open() as handle:
            return Mapping(json.load(handle))

    @property
    def content(self) -> Dict[str, str]:
        """
        Returns the mapping content.
        :return: Content
        """
        return self._content

    def __repr__(self) -> str:
        """
        Returns the printable representation of the mapping.
        :return: Representation
        """
        return 'Mapping({} items)'.format(len(self._content))

    def get(self, key) -> str:
        """
        Returns the item with the given key.
        :param key: Key
        :return: Item
        """
        return self._content[key]

    def get_metadata(self, seq_id: str, metadata_key: str, default: Optional[str] = None) -> str:
        """
        Returns the metadata value for the given key and sequence identifier.
        :param seq_id: Sequence identifier
        :param metadata_key: Metadata key
        :param default: Default value if key not present in metadata
        :return: None
        """
        if seq_id not in self._content:
            raise ValueError(f"No sample with id '{seq_id}' in mapping")
        metadata = json.loads(' '.join(self._content[seq_id].split(' ')[1:]))
        if metadata_key not in metadata:
            if default is None:
                raise ValueError(f"Key '{metadata_key}' not found in metadata")
            else:
                return default
        return metadata[metadata_key]
