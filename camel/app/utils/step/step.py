import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Union, Optional

from snakemake.io import Wildcards

from camel.app.io.toolio import ToolIO
from camel.app.tools.tool import Tool
from camel.app.utils.step.steplogging import StepLogging


@dataclass(frozen=True)
class StepOutput:
    """
    This class is used to keep an output of a step.
    """
    rule_name: str
    type: str
    key: str
    index: int
    hash: str
    wildcards: Optional[Wildcards] = None

    @property
    def wildcards_json(self) -> Union[None, str]:
        """
        Returns the wildcards as a JSON string.
        :return: Wildcards as string
        """
        if self.wildcards is None:
            return None
        return json.dumps({k: v for k, v in self.wildcards.items()})


class Step(object):
    """
    This class represents a step in a Snakemake pipeline. It executes a single tool.
    """

    def __init__(self, rule_name: str, tool: Tool, folder: Path, wildcards: Wildcards = None,
                 pipeline_output: bool = False, keys_log: Optional[List[str]] = None,
                 keys_no_log: Optional[List[str]] = None) -> None:
        """
        Initializes a step.
        :param rule_name: Name of the snakemake rule
        :param tool: Tool object of the tool that needs to be executed
        :param folder: Folder in which the step is being run
        :param wildcards: Wildcards object from snakemake
        :param pipeline_output: Boolean to indicate whether outputs are pipeline outputs
        :param keys_log: The output keys that should be logged (has preference over 'keys_no_log', by default all keys
            are logged
        :param keys_no_log: The output keys that should not be logged (by default all keys are logged)
        """
        self._name = rule_name
        self._tool = tool
        self._step_inputs = {}
        self._input_informs = {}
        self._pipeline_options = {}
        self._job_options = {}
        self._folder = folder
        self._pipeline_output = pipeline_output
        self._wildcards = wildcards
        self._keys_log = keys_log
        self._keys_no_log = keys_no_log

    @property
    def name(self) -> str:
        """
        Returns the name of this step.
        :return: Name
        """
        return self._name

    @property
    def outputs(self) -> Dict[str, List[ToolIO]]:
        """
        Returns the outputs of this step.
        :return: Outputs
        """
        return self._tool.tool_outputs

    @property
    def informs(self) -> dict:
        """
        Returns the informs of this step.
        :return: Informs
        """
        return self._tool.informs

    def add_inputs(self, dict_: dict) -> None:
        """
        Adds the inputs to the step
        :param dict_: Dictionary with input objects
        :return: None
        """
        self._step_inputs = dict_

    def add_informs(self, dict_: dict) -> None:
        """
        Adds informs to the step.
        :param dict_: Dictionary with the informs
        :return: None
        """
        self._input_informs = dict_
        logging.info("Inform added: {}".format(dict_))

    def _add_job_parameters(self) -> None:
        """
        Adds the job parameters.
        :return: None
        """
        if len(self._job_options) > 0:
            logging.info("Adding job parameters")
            self._tool.update_parameters(**self._job_options)

    def run_step(self) -> None:
        """
        Runs the current step.
        :return: None
        """
        StepLogging.attach_step_handlers(self._folder)
        self._tool.add_input_files(self._step_inputs)
        self._tool.add_input_informs(self._input_informs)
        logging.info("Default parameters loaded: {}".format(self._tool.parameter_overview))
        self._add_job_parameters()
        self._tool.run(self._folder)
        logging.info(f'Step output: {list(self.outputs.items())}')
        logging.info(f'Step informs: {list(self.informs.items())}')
        self._log_outputs()
        StepLogging.detach_step_handlers()

    def _log_outputs(self) -> None:
        """
        Logs the outputs in the database.
        :return: None
        """
        logging.info(f"Logging output for step '{self.name}'")
        for key, io_list in self.outputs.items():
            if not self._key_is_logged(key):
                logging.debug(f"Not logging output key: {key}")
                continue
            for index, io_out in enumerate(io_list):
                if not io_out.is_logged:
                    continue
                step_output = StepOutput(self._name, io_out.type_name, key, index, io_out.hash, self._wildcards)
                logging.info('Output log: {}'.format(step_output))

    def _key_is_logged(self, key: str) -> bool:
        """
        Checks whether the files with the given output key need to be logged.
        :param key: Output key to check
        :return: True/False
        """
        if (self._keys_log is None) and (self._keys_no_log is None):
            return True
        elif self._keys_log is not None:
            return key in self._keys_log
        else:
            return key not in self._keys_no_log
