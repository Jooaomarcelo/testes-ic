from typing import Any, List

from pymongo import UpdateOne
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.database import Database

from src.utils.app_error import AppError

COFFEE = "cafe"
COFFEE_YIELD = "producao"
REPORTS = "pipeline_reports"


# ===== Asynchronous Functions  =====
async def get_all_coffee_yield(db: AsyncDatabase) -> List[dict[str, Any]]:
	"""
	Fetches all documents from the 'producao' collection.

	:param db: The database connection.
	:return: A List of documents.
	:rtype: List[dict[str, Any]]
	"""
	docs = await db.get_collection(COFFEE_YIELD).find().to_list()
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
	doc = await db.get_collection(COFFEE).find_one(query)

	if not doc:
		raise AppError(status_code=404, detail="No data found for the given location")
	return doc


# ===== Synchronous Functions  =====
def get_point(
	db: Database, lng: float, lat: float, max_distance: int
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
	doc = db.get_collection(COFFEE).find_one(query)

	if not doc:
		raise AppError(status_code=404, detail="No data found for the given location")

	return doc


def update_points_time_series(
	db: Database,
	docs: List[dict[str, Any]],
):
	"""
	Updates documents in the 'cafe' collection by adding new time series data.

	If a document does not exist, it will be skipped.

	:param db: The database connection.
	:param docs: A list of documents. Each document must contain
				 'metadata.coordinates' for identification and a 'timeseries'
				 list to be appended.
	:return: The result of the bulk write operation.
	:rtype: BulkWriteResult | None
	"""
	if not docs:
		return

	operations = [
		UpdateOne(
			{"metadata.coordinates": doc["metadata"]["coordinates"]},
			{"$push": {"timeseries": {"$each": doc["timeseries"]}}},
		)
		for doc in docs
	]

	result = db.get_collection(COFFEE).bulk_write(operations)
	return result


def get_wtss_report(
	db: Database,
	job: str,
	coverage: str,
	start_date: str,
	end_date: str,
) -> dict[str, Any] | None:
	"""
	Retrieves a WTSS report document from the 'pipeline_reports' collection.
	:param db: The database connection.
	:param job: The job name.
	:param coverage: The coverage name.
	:param start_date: The start date of the report.
	:param end_date: The end date of the report.
	:return: The report document if found, else None.
	"""
	report = db.get_collection(REPORTS).find_one(
		{
			"job": job,
			"coverage": coverage,
			"start_date": start_date,
			"end_date": end_date,
		}
	)
	return report


def save_wtss_report(
	db: Database,
	job_key: dict[str, Any],
	report: dict[str, Any],
):
	"""
	Saves or updates a WTSS report document into the 'wtss_reports' collection.

	:param db: The database connection.
	:param report: The report document to be saved.
	"""
	db.get_collection(REPORTS).update_one(
		job_key,
		{"$setOnInsert": report},
		upsert=True,
	)


def update_wtss_report(
	db: Database,
	job_key: dict[str, Any],
	update_fields: dict[str, Any],
):
	"""
	Updates fields of a WTSS report document in the 'pipeline_reports' collection.

	:param db: The database connection.
	:param job_key: A dictionary containing the unique identifiers for the report
					(e.g., job, coverage, start_date, end_date).
	:param update_fields: A dictionary of fields to be updated in the report.
	"""
	db.get_collection(REPORTS).update_one(
		job_key,
		update_fields,
	)
