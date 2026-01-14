from typing import Any, List

from pymongo.asynchronous.database import AsyncDatabase

from src.utils.app_error import AppError


async def get_all_coffee_yield(db: AsyncDatabase) -> List[dict[str, Any]]:
	"""
	Fetches all documents from the 'producao' collection.

	:param db: The database connection.
	:return: A List of documents.
	:rtype: List[dict[str, Any]]
	"""
	docs = await db.get_collection("producao").find().to_list()
	return docs


async def get_point_time_series(
	db: AsyncDatabase, lng: float, lat: float, max_distance: int
) -> dict[str, Any]:
	"""
	Fetches a single document from the 'cafe' collection based on a geo query.

	:param db: The database connection.
	:param lng: Longitude for the geo query.
	:param lat: Latitude for the geo query.
	:param max_distance: Maximum distance for the geo query.
	:return: A document if found.
	:rtype: dict[str, Any]
	:raises AppError: If no document is found.
	"""
	# This query assumes a 2dsphere index on the 'metadata' field
	query = {
		"metadata": {
			"$near": {
				"$geometry": {
					"type": "Point",
					"coordinates": [lng, lat],
				},
				"$maxDistance": max_distance,
			},
		},
	}
	doc = await db.get_collection("cafe").find_one(query)

	if not doc:
		raise AppError(status_code=404, detail="No data found for the given location")
	return doc
