import abc
import inspect
import logging
from pathlib import Path
from typing import Dict, Optional, List, Union

from camel.app.error.invalidinputspecificationerror import InvalidInputSpecificationError
from camel.app.error.invalidparametererror import InvalidParameterError
from camel.app.error.toolexecutionerror import ToolExecutionError
from camel.app.io.toolio import ToolIO
from camel.app.io.tooliodirectory import ToolIODirectory
from camel.app.io.tooliofile import ToolIOFile
from camel.app.io.tooliovalue import ToolIOValue
from camel.app.service.yamltoolservice import YAMLToolService
from camel.app.utils.command import Command
from camel.config import config


class Tool(object, metaclass=abc.ABCMeta):
    """
    Contains the common functionality of tools.
    """

    def __init__(self, name: str) -> None:
        """
        Initializes a tool.
        """
        logging.debug(f'Initializing tool: {name}')
        self._name = name
        self._tool_service = self.get_tool_service()
        self._tool_command = self._tool_service.get_tool_command()
        self._dependencies = self._tool_service.get_dependencies()
        self._parameters = self._tool_service.get_default_parameters()
        self._version = self.get_version()
        self._tool_inputs: Dict[str, List[Union[ToolIOFile, ToolIOValue, ToolIODirectory, ToolIO]]] = {}
        self._tool_outputs: Dict[str, List[Union[ToolIOFile, ToolIOValue, ToolIODirectory, ToolIO]]] = {}
        self._informs = {'_name': self.name, '_version': self._version}
        self._input_informs = {}
        self._command = Command()
        self._folder = None

    @property
    def name(self) -> str:
        """
        Returns the name of this tool.
        :return: Name
        """
        return f'{self._name} {self._version}'

    @property
    def version(self) -> str:
        """
        Returns the tool version.
        :return: Version
        """
        return self._version

    @abc.abstractmethod
    def get_version(self) -> str:
        """
        Retrieves the tool version.
        :return: None
        """
        raise NotImplementedError()

    @property
    def tool_outputs(self) -> Dict[str, List[Union[ToolIOFile, ToolIOValue, ToolIODirectory, ToolIO]]]:
        """
        Returns the tool outputs.
        :return: Tool outputs
        """
        return self._tool_outputs

    @property
    def informs(self) -> dict:
        """
        Returns the tool informs.
        :return: Informs
        """
        return self._informs

    @property
    def dependencies(self) -> List[str]:
        """
        Returns a list of dependencies for this tool.
        :return: Dependencies
        """
        return self._dependencies

    @DeprecationWarning
    def get_dependency_version(self, name: str, full: bool = True) -> str:
        """
        Returns the version of the given dependency.
        :param name: Dependency name
        :param full: If True, the full dependency is returned (along with the name)
        :return: Dependency version
        """
        for full_dependency in self._dependencies:
            parts = full_dependency.split('/')
            name_dep = parts[0]
            if name == name_dep:
                version = 'default' if len(parts) == 0 else parts[1]
                return f'{name}/{version}' if full else version
        raise ValueError(f'Tool {self.name} has no dependency: {name}')

    @property
    def stdout(self) -> Optional[str]:
        """
        Returns the command line stdout.
        :return: Stdout
        """
        return self._command.stdout

    @property
    def stderr(self) -> Optional[str]:
        """
        Returns the command line stderr.
        :return: Stderr
        """
        return self._command.stderr

    @property
    def parameter_overview(self) -> str:
        """
        Returns an overview of the parameters as a string.
        :return: Parameters overview
        """
        return ', '.join(["{}: '{}'".format(p, self._parameters[p].value) for p in sorted(self._parameters)]) if \
            len(self._parameters) > 0 else '/'

    @property
    def folder(self) -> Path:
        """
        Returns the folder the tool needs to run in.
        :return: Path to the running folder
        """
        return self._folder

    def add_input_files(self, input_files: Dict[str, List[ToolIO]]) -> None:
        """
        Updates the input files for a tool.
        :param input_files: New input files
        :return: None
        """
        for key, items in input_files.items():
            if key in self._tool_inputs:
                self._tool_inputs[key] += items
            else:
                self._tool_inputs[key] = items

    def add_input_informs(self, informs: dict) -> None:
        """
        Updates the input informs for a tool.
        :param informs: New informs
        :return: None
        """
        self._input_informs.update(informs)

    def update_parameters(self, **kwargs: Union[str, int, None, bool, float, Dict[str, Union[str, int, None, bool, float]]]) -> None:
        """
        Updates the parameters for this tool.
        :param kwargs: Parameters in key value format
        :return: None
        """
        for parameter_name, new_value in kwargs.items():
            parameter = self._tool_service.get_parameter(parameter_name)
            if not parameter:
                raise InvalidParameterError("{} has no parameter '{}'".format(self._name, parameter_name))
            if new_value is False:
                if parameter_name not in self._parameters:
                    logging.warning("Cannot disable parameter '{}' (not present in parameters)".format(parameter_name))
                    continue
                logging.info("Disabling parameter: {}".format(parameter_name))
                del(self._parameters[parameter_name])
            else:
                if new_value is True or new_value is None:
                    parameter.value = None
                else:
                    parameter.value = str(new_value)
                if parameter_name not in self._parameters:
                    logging.info("Parameter '{}' added, value: {}".format(parameter_name, parameter.value))
                else:
                    old_value = self._parameters[parameter_name].value
                    logging.info("Parameter '{}' value '{}' changed to '{}'".format(
                        parameter_name, old_value, new_value))
                self._parameters[parameter_name] = parameter

    def clear_parameters(self) -> None:
        """
        Clears all the parameters of the given tool.
        :return: None
        """
        logging.info("Removing {} parameters".format(len(self._parameters)))
        self._parameters.clear()

    def run(self, folder: Path = Path.cwd()) -> None:
        """
        Runs this tool.
        :param folder: Folder to run the tool in.
        :return: None
        """
        self._folder = folder
        logging.info(f'Running tool {self.name}')
        logging.info(f'Working directory: {self._folder}')
        logging.info(f'Tool parameters: {self.parameter_overview}')
        self._check_parameters()
        self._check_input()
        self._execute_tool()
        self._check_output()

    @DeprecationWarning
    def get_outputs(self, key: str) -> List[ToolIO]:
        """
        Returns the outputs with the given key.
        :param key: output key
        :return: Output list
        """
        if key not in self._tool_outputs:
            raise ValueError(f"No output file with key '{key}' found")
        return self._tool_outputs[key]

    def get_tool_data_path(self) -> Path:
        """
        Returns the path of the tool data for the tool with the given name and version.
        :return: Path
        """
        yaml_path = Path(inspect.getfile(self.__class__).replace('.py', '.yml'))
        if not yaml_path.is_file():
            raise FileNotFoundError(f"Tool data file for '{self.name}' not found ({yaml_path})")
        return yaml_path

    def get_tool_service(self) -> YAMLToolService:
        """
        Returns the tool service for the tool with the given name and version.
        :return: Tool service
        """
        return YAMLToolService(self.get_tool_data_path())

    def _build_dependencies(self) -> str:
        """
        Builds the dependencies.
        :return: Command to load dependencies
        """
        return '' if len(self._dependencies) == 0 else 'module load {}; '.format(' '.join(self._dependencies))

    def _build_options(self, excluded_parameters: List[str] = None, delimiter: str = ' ') -> List[str]:
        """
        Builds the options string.
        :parameter delimiter: Delimiter between option and value
        :return: Options string
        """
        options = []
        for name, parameter in sorted(self._parameters.items(), key=lambda x: x[1].p_index):
            if (excluded_parameters is not None) and (name in excluded_parameters):
                continue
            if parameter.value is not None:
                options.append(parameter.option + delimiter + str(parameter.value))
            else:
                options.append(parameter.option)
        return options

    def _execute_command(self, folder: Path = None) -> None:
        """
        Executes the command.
        :return: None
        """
        if folder is None:
            folder = self._folder
        if self._command.command is None:
            raise ValueError("Command is 'None'.")
        if config.get('use_lmod', True):
            self._command.command = self._build_dependencies() + self._command.command
        self._informs['_command'] = self._command.command
        self._command.run(folder)
        self._check_command_output()

    def _check_command_output(self) -> None:
        """
        Checks if the command was executed successfully.
        :return: None
        """
        if self.stderr != '':
            raise ToolExecutionError("Command execution failed (stderr: {}).".format(self.stderr))
        elif self._command.returncode != 0:
            raise ToolExecutionError("Command execution failed (Exit code: {})".format(self._command.returncode))

    @abc.abstractmethod
    def _execute_tool(self):
        """
        Executes this tool.
        :return: None
        """
        raise NotImplementedError("Method should be implemented by subclass.")

    def _check_parameters(self) -> None:
        """
        Checks if the tool parameters are valid.
        :return: None
        """
        mandatory_parameters = self._tool_service.get_names_mandatory_parameter()
        for mandatory_parameter in mandatory_parameters:
            if mandatory_parameter not in self._parameters:
                raise ValueError("Mandatory parameter {} not set".format(mandatory_parameter))

    def _check_input(self) -> None:
        """
        Checks if the tool input is valid.
        :return: None
        """
        for input_key, input_list in self._tool_inputs.items():
            for tool_input in input_list:
                if not isinstance(tool_input, ToolIO):
                    raise InvalidInputSpecificationError("Tool input '{}' is not a ToolIO object".format(tool_input))
                if tool_input is None:
                    raise InvalidInputSpecificationError("Tool input with key {} is None".format(input_key))
                if not tool_input.is_valid():
                    raise InvalidInputSpecificationError("Invalid tool input with key {}: {}".format(
                        input_key, tool_input))

    def _check_output(self) -> None:
        """
        Checks if the output is valid.
        :return: None
        """
        for output_key, output_list in self._tool_outputs.items():
            for tool_output in output_list:
                if tool_output is None:
                    raise ValueError("Tool output with key {} is None".format(output_key))
                if not isinstance(tool_output, ToolIO):
                    raise ValueError("'{} {}' is not a tool output object".format(tool_output, type(tool_output)))
                if not tool_output.is_valid():
                    raise ValueError("Invalid tool output with key {}: {}".format(output_key, tool_output))
