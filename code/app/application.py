"""Shared application startup for price collection."""

import time

from utils import custom_logging
from utils.configuration import Configuration

logger = custom_logging.get_logger(__name__)


def run() -> None:
    config = Configuration()
    logger.info("Fichero de configuración: %s", config.source_path)
    logger.info("database.schema: %s", config.get("database.schema", cast=str))
    logger.info(
        "collection.interval_seconds: %s",
        config.get("collection.interval_seconds", cast=int),
    )
    logger.info(
        "collection.retry_delay_seconds: %s",
        config.get("collection.retry_delay_seconds", cast=int),
    )

    while True:
        logger.info("Empezando a capturar precios de internet")
        time.sleep(10)
