import logging
from pathlib import Path

from camel.config import config


def initialize_logging() -> None:
    """
    Initializes the logging.
    :return: None
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format=config['logging']['format']
    )


def add_filehandler(dir_logs: Path, db_key: str) -> logging.Handler:
    """
    Adds a file handler to the default logger.
    :param dir_logs: Directory to store logs
    :param db_key: Database key
    :return: Handler
    """
    handler = logging.FileHandler(str(dir_logs / f'update_{db_key}.log'))
    handler.setFormatter(logging.Formatter(config['logging']['format']))
    logging.getLogger().addHandler(handler)
    return handler
