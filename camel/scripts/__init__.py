from camel.app import loggingutils
from camel.scripts.maingenedetection import MainGeneDetection
from camel.scripts.mainmakegenedetectiondb import MainMakeGeneDetectionDB


def main_gene_detection() -> None:
    """
    Entry point for main gene detection script.
    :return: None
    """
    loggingutils.initialize_logging()
    main = MainGeneDetection()
    main.run()


def main_create_db() -> None:
    """
    Entry point for main gene detection script.
    :return: None
    """
    loggingutils.initialize_logging()
    main = MainMakeGeneDetectionDB()
    main.run()
