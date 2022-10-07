import abc
from abc import ABCMeta


class ToolIO(object, metaclass=ABCMeta):
    """
    Class that represents the input or output of a tool.
    """

    def __init__(self, logged: bool) -> None:
        """
        Initializes a tool input / output.
        :param logged: If true, the output can be logged
        """
        self._logged = logged

    @property
    def is_logged(self) -> bool:
        """
        Returns True if the output is logged.
        :return: True / False
        """
        return self._logged

    @abc.abstractmethod
    def is_valid(self) -> bool:
        """
        Checks whether the tool input / output is valid.
        :return: None
        """
        pass

    @property
    @abc.abstractmethod
    def hash(self) -> str:
        """
        Returns the hash value.
        :return: Hash value
        """
        pass

    @property
    @abc.abstractmethod
    def type_name(self) -> str:
        """
        Returns the type of the IO object.
        :return: Type value
        """
        pass
