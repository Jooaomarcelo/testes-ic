"""Application logging configuration module."""

import logging
from os import getenv as env


def setup_logging():
	"""Configure the application logging system.

	:return: Configured logger
	:rtype: logging.Logger
	"""
	logging.basicConfig(
		level=logging.INFO
		if env("ENV", "development") == "production"
		else logging.DEBUG,
		format="%(levelname)s - %(asctime)s - %(name)s - %(message)s",
	)

	# Silenciar logs verbosos do pymongo
	logging.getLogger("pymongo").setLevel(logging.WARNING)
	logging.getLogger("aio_pika").setLevel(logging.WARNING)
	logging.getLogger("aiormq").setLevel(logging.WARNING)

	return logging.getLogger(__name__)
