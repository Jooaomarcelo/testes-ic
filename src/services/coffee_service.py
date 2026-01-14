from pymongo.asynchronous.database import AsyncDatabase

from src.models.coffee import PointTimeSeriesFetch
from src.repos import coffee_repo
from src.utils.app_error import AppError


async def get_coffee_yield(db: AsyncDatabase):
	"""
	Service to get all coffee yield data.

	:param db: The database connection.
	:return: A list of coffee yield documents.
	"""
	return await coffee_repo.get_all_coffee_yield(db)


async def get_point_time_series(
	db: AsyncDatabase, point_time_series_fetch: PointTimeSeriesFetch
):
	"""
	Service to get point time series data.

	:param db: The database connection.
	:param lng: Longitude for the geo query.
	:param lat: Latitude for the geo query.
	:param max_distance: Maximum distance for the geo query.
	:return: A point time series document.
	:raises AppError: If no data is found for the given parameters.
	"""
	lat, lng, max_distance = point_time_series_fetch.model_dump().values()

	point_data = await coffee_repo.get_point_time_series(db, lng, lat, max_distance)

	if not point_data:
		raise AppError(404, "No data found for the given parameters")

	return point_data
