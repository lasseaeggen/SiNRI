import logging
import sys


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
    )


def get_logger(name):
    setup_logging()
    logger = logging.getLogger(name)
    return logger
