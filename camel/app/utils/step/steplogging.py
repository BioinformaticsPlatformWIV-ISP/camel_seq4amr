import logging
import logging.config
from pathlib import Path

import yaml


class StepLogging(object):
    """
    Manages the various logs.
    """
    _step_handlers = []
    _pipeline_handlers = []

    @staticmethod
    def initialize(config_file: Path):
        """
        Initializes the log manager.
        :param config_file: Configuration file
        :return: None
        """
        with open(config_file, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
        StepLogging._step_handlers = [h for h in logging.getLogger().handlers if h.get_name().startswith('step')]
        StepLogging._pipeline_handlers = [h for h in logging.getLogger().handlers if h.get_name().startswith('pipeline')]
        StepLogging.detach_step_handlers()
        StepLogging.detach_pipeline_handlers()
        logging.info("Log manager initialized")

    @staticmethod
    def attach_step_handlers(folder: Path) -> None:
        """
        Attaches the step handlers and updates the log location.
        :param folder: Folder to store the logs
        :return: None
        """
        for step_handler in StepLogging._step_handlers:
            filename = Path(step_handler.baseFilename).name
            step_handler.close()
            step_handler.baseFilename = str(folder / filename)
            logging.getLogger().addHandler(step_handler)

    @staticmethod
    def detach_step_handlers() -> None:
        """
        Detaches the step handlers.
        :return: None
        """
        for step_handler in StepLogging._step_handlers:
            if step_handler in logging.getLogger().handlers:
                logging.getLogger().handlers.remove(step_handler)

    @staticmethod
    def attach_pipeline_handlers(folder: Path) -> None:
        """
        Attaches the pipeline handlers and updates the log location.
        :param folder: Folder to store the logs
        :return: None
        """
        for pipeline_handler in StepLogging._pipeline_handlers:
            filename = Path(pipeline_handler.baseFilename).name
            pipeline_handler.close()
            pipeline_handler.baseFilename = str(folder / filename)
            logging.getLogger().addHandler(pipeline_handler)

    @staticmethod
    def detach_pipeline_handlers() -> None:
        """
        Detaches the pipeline handlers.
        :return: None
        """
        for pipeline_handler in StepLogging._pipeline_handlers:
            if pipeline_handler in logging.getLogger().handlers:
                logging.getLogger().handlers.remove(pipeline_handler)
