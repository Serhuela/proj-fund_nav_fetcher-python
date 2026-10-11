"""Shared application startup for price collection."""

import time

from utils import custom_logging

logger = custom_logging.get_logger(__name__)


def run() -> None:
    while True:
        logger.info("Empezando a capturar precios de internet")
        time.sleep(10)
