import logging
import time
from datetime import timedelta
from os import getenv as env
from typing import List, Literal

import geopandas as gpd
from pymongo import MongoClient
from requests.exceptions import HTTPError
from shapely.geometry import MultiPolygon, Polygon
from wtss import WTSS

import src.repos.coffee_repo as coffee_repo
from src.models.bdc import WTSSReport
from src.utils.date_now import get_utc_now

logger = logging.getLogger(__name__)


def indedexes_to_process(
	mode: Literal["full", "resume", "retry_failed"],
	existing_report: WTSSReport | None,
	total_polygons: int,
) -> List[int] | range:
	"""
	Determines which polygon indexes to process based on the specified mode and existing report.

	:param mode: Operation mode
	:type mode: Literal["full", "resume", "retry_failed"]
	:param existing_report: Existing WTSS report, if any
	:type existing_report: WTSSReport | None
	:param total_polygons: Total number of polygons to process
	:type total_polygons: int
	:return: Set or range of polygon indexes to process
	:rtype: set[int] | range
	"""
	if mode == "resume" and existing_report:
		start_index = (
			existing_report.get("summary", {}).get("last_processed_index", -1) + 1
		)
		return range(start_index, total_polygons)

	elif mode == "retry_failed" and existing_report:
		return sorted({err["index"] for err in existing_report["errors"]})

	else:  # full
		return range(total_polygons)


def run_wtss(
	gdf: gpd.GeoDataFrame,
	start_date: str,
	end_date: str,
	mode: Literal["full", "resume", "retry_failed"] = "full",
):
	"""
	Runs the WTSS data retrieval and storage process.

	:param gdf: Geopandas DataFrame containing geometries
	:type gdf: gpd.GeoDataFrame
	:param start_date: Start date for data retrieval
	:type start_date: str
	:param end_date: End date for data retrieval
	:type end_date: str
	:param mode: Operation mode
	:type mode: Literal["full", "resume", "retry_failed"]
	"""
	# Counters and stats
	total_docs = 0
	success = 0
	failed = 0
	empty_series = 0
	errors = []

	# Mongo DB connection
	client = MongoClient(env("DB_URL", "mongodb://mongo:27017/"))
	db = client[env("DB_NAME", "campo_vertentes")]

	# WTSS service connection
	service = WTSS(env("WTSS_URL", "https://data.inpe.br/bdc/wtss/v4/"))
	coverage_name = "S2-16D-2"
	coverage = service[coverage_name]

	geometries = [
		geom for geom in gdf["geometry"] if isinstance(geom, (Polygon, MultiPolygon))
	]
	total_polygons = len(geometries)

	# Retrieve previous WTSS report if exists
	job_key = {
		"job": "wtss",
		"coverage": coverage_name,
		"start_date": start_date,
		"end_date": end_date,
	}

	existing_report = coffee_repo.get_wtss_report(db, **job_key)

	if mode == "full" and not existing_report:
		report = WTSSReport(
			# TODO: Ajustar modelo para diferenciar geometrias (admin vs cron)
			**job_key,
			status="partial",
			summary={
				"total_polygons": total_polygons,
				"success": success,
				"failed": failed,
			},
			errors=errors,
			created_at=get_utc_now(),
			updated_at=get_utc_now(),
		)
		coffee_repo.save_wtss_report(db, job_key, report.model_dump())

	indexes = indedexes_to_process(mode, existing_report, total_polygons)

	start_time = time.time()

	logger.info(
		"WTSS job started",
		extra={
			**job_key,
			"mode": mode,
			"total_polygons": total_polygons,
			"indexes_to_process": len(indexes),
		},
	)

	for i in indexes:
		geom = geometries[i]
		geocodigo = str(gdf.iloc[i].get("CD_MUN", "unknown"))
		polygon_start_time = time.time()

		logger.info(
			f"Processing polygon {i + 1}/{total_polygons} (geocodigo={geocodigo})"
		)

		try:
			ts = coverage.ts(
				attributes=(
					"NDVI",
					"EVI",
					"B04",
					"B08",
					"B03",
				),
				geom=geom,
				start_datetime=start_date,
				end_datetime=end_date,
			)

			df = ts.df()

			if df.empty:
				empty_series += 1
				logger.info("Série temporal vazia para este polígono.")
				if empty_series > 5:
					logger.info("Muitas séries vazias. Interrompendo o processamento.")
					break

				continue

			pivoted = (
				df.pivot_table(
					index=["geometry", "datetime"],
					columns="attribute",
					values="value",
					aggfunc="first",
				)
				.reset_index()
				.rename(
					columns={
						"NDVI": "ndvi",
						"EVI": "evi",
						"B03": "green",
						"B04": "red",
						"B08": "nir",
						"datetime": "timestamp",
					},
					inplace=True,
				)
			)

			# Agrupar dados por pixel (ponto)
			docs = []

			for pixel, group in pivoted.groupby("geometry"):
				docs.append(
					{
						"geocodigo": geocodigo,
						"metadata": {
							"type": "Point",
							"coordinates": list(pixel.coords[0]),
						},
						"timeseries": group.drop(columns=["geometry"]).to_dict(
							orient="records"
						),
					}
				)

			if docs:
				result = coffee_repo.update_points_time_series(db, docs)
				success += 1
				total_docs += result.modified_count

				logger.info(
					f"Polygon {i + 1} processed successfully "
					f"(docs={len(docs)}, modified={result.modified_count}, "
					f"time={time.time() - polygon_start_time:.2f}s)"
				)
			else:
				logger.warning(
					f"No documents generated for polygon {i + 1} (geocodigo={geocodigo})"
				)

		except HTTPError as e:
			failed += 1
			error_entry = {
				"polygon_index": i,
				"geocodigo": geocodigo,
				"error": str(e),
			}
			errors.append(error_entry)
			logger.exception(
				f"Error processing polygon {i + 1} (geocodigo={geocodigo})"
			)

			# Checkpoint
			coffee_repo.update_wtss_report(
				db,
				job_key,
				{
					"$push": {"errors": error_entry},
					"$set": {
						"summary.last_processed_index": i,
						"updated_at": get_utc_now(),
					},
					"$inc": {"summary.failed": 1},
				},
			)
			break  # Stop processing on HTTP errors

		except Exception as e:
			failed += 1
			error_entry = {
				"polygon_index": i,
				"geocodigo": geocodigo,
				"error": str(e),
			}
			errors.append(error_entry)
			logger.exception(
				f"Error processing polygon {i + 1} (geocodigo={geocodigo})"
			)

			# Checkpoint
			coffee_repo.update_wtss_report(
				db,
				job_key,
				{
					"$push": {"errors": error_entry},
					"$set": {
						"updated_at": get_utc_now(),
					},
					"$inc": {"summary.failed": 1},
				},
			)

	total_time = time.time() - start_time

	status = "success" if failed == 0 else "partial" if success > 0 else "failed"

	info = {
		"status": status,
		"success": success,
		"failed": failed,
		"total_time_seconds": round(total_time, 2),
		"total_time_formatted": str(timedelta(seconds=total_time)).split(".")[0],
		"total_docs_updated": total_docs,
	}
	logger.info(f"WTSS job finished:\n{info}", extra=info)

	# Final report update
	coffee_repo.update_wtss_report(
		db,
		job_key,
		{
			"$set": {
				"status": status,
				"summary.success": success,
				"updated_at": get_utc_now(),
			}
		},
	)
