"""Application logging configuration module."""

import logging

from ..core.config import settings


def setup_logging():
    """Configure the application logging system.

    :return: Configured logger
    :rtype: logging.Logger
    """
    logging.basicConfig(
        level=logging.INFO if settings.env == "production" else logging.DEBUG,
        format="%(levelname)s - %(asctime)s - %(name)s - %(message)s",
    )

    # Silenciar logs verbosos do pymongo
    logging.getLogger("pymongo").setLevel(logging.WARNING)

    return logging.getLogger(__name__)
