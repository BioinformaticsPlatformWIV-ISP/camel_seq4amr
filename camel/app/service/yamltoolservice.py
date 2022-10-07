from collections import OrderedDict
from pathlib import Path
from typing import List, Optional

import yaml

from camel.app.tools.parameter import Parameter


class YAMLToolService(object):
    """
    This tool loads tool related data from a YAML file.
    """

    def __init__(self, tool_data_path: Path) -> None:
        """
        Initializes tool service class assigning the module
        :param tool_data_path: Path with the tool data
        :return: None
        """
        with tool_data_path.open() as handle:
            self._tool_data = yaml.safe_load(handle)

    @property
    def tool_id(self) -> Optional[str]:
        """
        The tool id is set to 'None' when running with a YAML service.
        :return: None
        """
        return None

    def get_tool_command(self) -> str:
        """
        Returns the tool command.
        :return: Tool command
        """
        return self._tool_data['tool_command']

    def get_dependencies(self) -> List[str]:
        """
        Gets the dependencies for the tool from the database
        :return: String with whitespace separated list of dependencies
        """
        return self._tool_data['dependencies']

    def get_default_parameters(self) -> OrderedDict:
        """
        Returns the default parameters for this tool.
        :return: Default parameters
        """
        param_dict = OrderedDict()
        for p_name, p_data in sorted(self._tool_data['parameters'].items(), key=lambda x: x[1].get('p_index', 0)):
            if p_data['default'] is True:
                param_dict[p_name] = Parameter(p_name, p_data['option'], p_data['value'], p_data.get('p_index', 0))
        return param_dict

    def get_names_mandatory_parameter(self) -> List[str]:
        """
        Returns all the default parameters.
        :return: Default parameter names
        """
        return [p_name for p_name, p_data in self._tool_data['parameters'].items() if p_data['mandatory'] is True]

    def get_parameter(self, parameter_name) -> Optional[Parameter]:
        """
        Returns the parameter with the given name.
        :param parameter_name: Parameter name
        :return: Parameter
        """
        try:
            p_data = self._tool_data['parameters'][parameter_name]
            return Parameter(parameter_name, p_data['option'], p_data['value'], p_data.get('p_index', 0))
        except KeyError:
            return None
