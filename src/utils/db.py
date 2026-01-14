"""MongoDB database connection utilities module."""

import logging

from pymongo import AsyncMongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from starlette.requests import Request

from ..core.config import settings

logger = logging.getLogger(__name__)


async def create_pool() -> AsyncMongoClient:
	"""
	Function to create a MongoDB connection pool.

	:return: MongoDB client instance
	:rtype: AsyncMongoClient
	:raises ValueError: If DB_URL is not set
	:raises ConnectionError: If unable to connect to DB
	"""
	mongo_url: str | None = settings.db_url

	if mongo_url is None:
		raise ValueError("DB_URL environment variable is not set")

	try:
		client = AsyncMongoClient(
			mongo_url,
			serverSelectionTimeoutMS=5000,  # 5 seconds timeout
			connectTimeoutMS=5000,
		)

		# Testa a conexão
		await client.admin.command("ping")
		logger.info("Successfully connected to MongoDB")

		return client

	except (ConnectionFailure, ServerSelectionTimeoutError) as e:
		logger.error(f"Failed to connect to MongoDB: {e}")
		raise ConnectionError(f"Unable to connect to MongoDB at {mongo_url}") from e
	except Exception as e:
		logger.error(f"Unexpected error connecting to MongoDB: {e}")
		raise


async def close_pool(client: AsyncMongoClient):
	"""
	Function to close the MongoDB connection pool.

	:param client: MongoDB client instance
	:type client: AsyncMongoClient
	"""
	await client.close()


async def get_conn(request: Request):
	"""
	Dependency to get a MongoDB client from the app state.

	:param request: Starlette request object
	:type request: Request
	:return: MongoDB client instance
	:rtype: AsyncMongoClient
	"""
	return request.app.state.pool.get_database(settings.db_name)
