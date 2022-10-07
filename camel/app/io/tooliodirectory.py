from pathlib import Path

from camel.app.io.toolio import ToolIO
from camel.app.utils.fileutils import FileUtils


class ToolIODirectory(ToolIO):
    """
    Class that represents an input / output directory of a tool.
    """

    def __init__(self, path: Path, logged: bool = True) -> None:
        """
        Initializes a tool input / output directory.
        :param path: Path to the directory
        :param logged: If True, the output can be logged
        """
        super(ToolIODirectory, self).__init__(logged)
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
        return f'ToolIODirectory("{self.path}")'

    def is_valid(self) -> bool:
        """
        Checks if the tool input / output directory is valid.
        :return: True if valid
        """
        return self.exists

    @property
    def hash(self) -> str:
        """
        Returns the hash value.
        :return: Hash value
        """
        return FileUtils.hash_directory(self.path)

    @property
    def path(self) -> Path:
        """
        Returns the path to the input / output directory.
        :return: Path
        """
        return self._path

    @property
    def basename(self) -> str:
        """
        Returns the basename of the input / output directory.
        :return: Basename
        """
        return self.path.name

    @property
    def exists(self) -> bool:
        """
        Checks whether this directory exists.
        :return: True if the directory exists, False otherwise
        """
        return self._path.is_dir()

    @property
    def type_name(self) -> str:
        """
        Returns the type of the IO object.
        :return: Type value
        """
        return 'dir'
