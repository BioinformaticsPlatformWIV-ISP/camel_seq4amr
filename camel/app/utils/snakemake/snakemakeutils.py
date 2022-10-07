import logging
import pickle
from pathlib import Path
from typing import Any, Optional, List

from camel.app.io.tooliodirectory import ToolIODirectory
from camel.app.io.tooliofile import ToolIOFile
from camel.app.io.tooliovalue import ToolIOValue
from camel.app.tools.tool import Tool


class SnakemakeUtils(object):

    """
    This class contains utility functions for working with snakemake and CAMEL.
    """

    @staticmethod
    def dump_object(obj: Any, path: Path) -> None:
        """
        Dumps an object in a pickle.
        :param obj: Object to dump
        :param path: Path to store the pickle
        :return: None
        """
        logging.debug(f"Dumping object '{obj!r}' in file '{path}'")
        with path.open('wb') as handle:
            pickle.dump(obj, handle)

    @staticmethod
    def load_object(path: Path) -> Any:
        """
        Loads the object from the given pickle.
        :param path: Path
        :return: Object
        """
        logging.debug(f"Loading object from file '{path}'")
        with path.open('rb') as handle:
            obj = pickle.load(handle)
        logging.debug(f"'{obj!r}' loaded")
        return obj

    @staticmethod
    def get_io_object(value: Any) -> Any:
        """
        Returns the value as a CAMEL IO object.
        - If it is a file path a ToolIOFile object is returned
        - If it is a directory path a ToolIOFolder object is returned
        - Else a ToolIOValue is returned
        :param value: Input value
        :return: ToolIO object
        """
        path = Path(value)
        if path.is_file():
            converted_value = ToolIOFile(value)
        elif path.is_dir():
            converted_value = ToolIODirectory(value)
        else:
            converted_value = ToolIOValue(value)
        logging.info(f"'{value}' converted to {converted_value!r}")
        return converted_value

    @staticmethod
    def add_pickle_input(tool: Tool, key: str, path: Path, optional: bool = False) -> None:
        """
        Adds a pickled input to a tool. For optional input whose value is empty, it is skipped.
        :param tool: Tool
        :param key: Key
        :param path: Pickle path
        :param optional: True for optional input, False otherwise
        :return: None
        """
        logging.debug(f"Adding pickled input with key '{key}' from file '{path}' to tool '{tool.name}'")
        value = SnakemakeUtils.load_object(path)
        if optional and len(value) == 0:
            logging.debug(f"Optional Input '{key}' empty, skipped")
        else:
            tool.add_input_files({key: value})

    @staticmethod
    def dump_tool_output(tool: Tool, key: str, path: Path) -> None:
        """
        Dumps a tool output to a Camel IO pickle.
        :param tool: Tool
        :param key: Key
        :param path: Pickle path
        :return: None
        """
        logging.debug("Dumping output with key '{}' from tool '{}' to Camel IO pickle '{}'".format(
            key, tool.name, path))
        if key not in tool.tool_outputs:
            raise KeyError(f"Tool '{tool.name}' has no output '{key}'")
        SnakemakeUtils.dump_object(tool.tool_outputs[key], path)

    @staticmethod
    def add_pickle_inputs(tool: Tool, snake_input: Any, keys: Optional[List[str]] = None,
                          excluded_keys: Optional[List[str]] = None, optionals: Optional[List[str]] = None) -> None:
        """
        Adds pickled inputs from the snakemake input. If 'optionals' is specified, any optional input in that
        list will be skipped if its value is empty (no input file).
        :param tool: Tool
        :param snake_input: Snakemake input
        :param keys: Keys to add. If None, all keys are added
        :param excluded_keys: For the keys in this list the files are not added
        :param optionals: list of keys specifying optional inputs
        :return: None
        """
        logging.info("Adding pickled inputs from snakemake input")
        if optionals is None:
            optionals = []
        if keys is None:
            keys = snake_input.keys()
        for key in keys:
            logging.debug(f"Adding input '{key}'")
            if key not in snake_input.keys():
                raise KeyError(f"Key '{key}' not found in snakemake input")
            if (excluded_keys is not None) and (key in excluded_keys):
                continue
            with open(snake_input[key], 'rb') as handle:
                value = pickle.load(handle)
            if key.startswith('INFORMS'):
                inform_key = '_'.join(key.split('_')[1:])
                tool.add_input_informs({inform_key: value})
                logging.debug(f"Informs '{value!r}' added")
            else:
                if key in optionals and len(value) == 0:
                    logging.debug(f"Optional Input '{key!r}' empty, skipped")
                    continue
                tool.add_input_files({key: value})
                logging.debug(f"Input '{value!r}' added")

    @staticmethod
    def dump_tool_outputs(tool: Tool, snake_output: Any, keys: Optional[List[str]] = None,
                          ignore_missing_output: bool = False) -> None:
        """
        Dumps the tool outputs in pickles.
        :param tool: Tool
        :param snake_output: Snake output
        :param keys: Keys to dump
        :param ignore_missing_output: If False, an error is raised when an output is not generated
        :return: None
        """
        logging.info("Dumping tool outputs")
        if keys is None:
            keys = snake_output.keys()
        for key in keys:
            if key in tool.tool_outputs:
                with open(snake_output[key], 'wb') as handle:
                    pickle.dump(tool.tool_outputs[key], handle)
            elif key == 'INFORMS':
                with open(snake_output[key], 'wb') as handle:
                    pickle.dump(tool.informs, handle)
            else:
                message = f"Output '{key}' not generated"
                if ignore_missing_output is True:
                    logging.warning(message)
                else:
                    raise ValueError(message)

    @staticmethod
    def pickle_snake_input(snake_input: Any, snake_output: Any, keys: Optional[List[str]] = None) -> None:
        """
        Converts snakemake input to CAMEL IO pickles.
        For every key, it will attempt to convert every value to an IO object (see IO object function) and store the
        generated pickle in the corresponding file specified in the snake output.
        :param snake_input: Snake input
        :param snake_output: Snake output
        :param keys: If specified, only those keys are converted.
        :return: None
        """
        logging.info(f"Converting snake input '{snake_input!r}' to pickles")
        if keys is None:
            keys = snake_input.keys()
        for key in keys:
            if key not in snake_input.keys():
                raise KeyError(f"Key '{key}' not found in snakemake input")
            input_list = snake_input[key]
            if key not in snake_output.keys():
                raise ValueError(f"Output key '{key}' not found.")
            list_io_objects = [SnakemakeUtils.get_io_object(i) for i in input_list]
            SnakemakeUtils.dump_object(list_io_objects, snake_output[key])

    @staticmethod
    def run_tool(tool: Tool, snake_input: Any, snake_output: Any, working_dir: Path) -> None:
        """
        Runs a tool and collects / converts the output and input.
        :param tool: Tool
        :param snake_input: Snakemake input
        :param snake_output: Snakemake output
        :param working_dir: Working directory
        :return: None
        """
        logging.info(f"Running tool: {tool.name}")
        SnakemakeUtils.add_pickle_inputs(tool, snake_input)
        tool.run(working_dir)
        SnakemakeUtils.dump_tool_outputs(tool, snake_output)
