import os
from pathlib import Path

import humanize

from camel.app.io.toolio import ToolIO
from camel.app.utils.fileutils import FileUtils


class ToolIOFile(ToolIO):
    """
    Class that represents an input / output file of a tool.
    """

    def __init__(self, path: Path, logged: bool = True) -> None:
        """
        Initializes a tool input / output file.
        :param path: Path to the file
        :param logged: If True, the output can be logged
        """
        super(ToolIOFile, self).__init__(logged)
        self._path = path.absolute()

    def __str__(self) -> str:
        """
        String representation
        :return: String representation
        """
        return str(self._path)

    def __repr__(self) -> str:
        """
        Internal representation
        :return: Internal representation
        """
        return f'ToolIOFile("{self.path}", {humanize.naturalsize(self.size)})'

    def is_valid(self) -> bool:
        """
        Checks if the tool input / output file is valid.
        :return: True if valid
        """
        return self.exists

    @property
    def path(self) -> Path:
        """
        Returns the path to the input / output file.
        :return: Path
        """
        return self._path

    @property
    def basename(self) -> str:
        """
        Returns the basename of the input / output file.
        :return: Basename
        """
        return self.path.name

    @property
    def file_extension(self) -> str:
        """
        Returns the file extension.
        :return: File extension
        """
        return self.path.suffix

    @property
    def exists(self) -> bool:
        """
        Checks whether this file exists.
        :return: True if the file exists, False otherwise
        """
        return os.path.isfile(self._path)

    @property
    def size(self) -> int:
        """
        Returns the size of this file.
        :return: Size
        """
        return self.path.stat().st_size

    @property
    def hash(self) -> str:
        """
        Returns the hash value of this file.
        :return: Hash
        """
        return FileUtils.hash_file(self.path)

    @property
    def type_name(self) -> str:
        """
        Returns the type of the IO object.
        :return: Type value
        """
        return 'file'
