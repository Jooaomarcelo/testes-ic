from os import getenv as env
from pathlib import Path

import geopandas as gpd
from celery.utils.log import get_task_logger

from src.models.bdc import (
	BDCBasePayload,
	WTSSPayload,
	parse_stac_payload,
	parse_wtss_payload,
)
from src.services.stac_service import run_stac
from src.services.wtss_service import run_wtss
from src.worker import app

logger = get_task_logger(__name__)

CAMPO_VERTENTES_SHP = Path(env("CAMPO_VERTENTES_SHAPEFILE_PATH"))
COFFEE_SHP = Path(env("COFFEE_SHAPEFILE_PATH"))


@app.task
def bdc_cron():
	"""
	Celery task to enqueue WTSS and STAC tasks for BDC data processing.

	:return: Confirmation message
	:rtype: str
	"""
	from datetime import timedelta

	from models.bdc import WTSSCronPayload
	from src.utils.date_now import get_utc_now

	start_date = (get_utc_now() - timedelta(days=7)).isoformat().split("T")[0]
	end_date = get_utc_now().isoformat().split("T")[0]

	wtss_payload = WTSSCronPayload(
		start_date=start_date,
		end_date=end_date,
	)

	stac_payload = BDCBasePayload(
		start_date=start_date,
		end_date=end_date,
	)

	logger.info(f"Enqueuing WTSS task with payload: {wtss_payload.model_dump_json()}")
	logger.info(f"Enqueuing STAC task with payload: {stac_payload.model_dump_json()}")

	handle_stac.delay(stac_payload.model_dump())
	handle_wtss.delay(wtss_payload.model_dump())

	return "BDC cron tasks enqueued."


@app.task
def handle_wtss(payload: dict):
	"""
	Processing task for WTSS queue messages.

	:param payload: The payload containing WTSS task details
	:type payload: dict
	:return: Confirmation message
	:rtype: str
	"""
	try:
		# A validação acontece dentro da task agora
		parsed_payload: WTSSPayload = parse_wtss_payload(payload)
		logger.info(
			f"Received WTSS task with payload: {parsed_payload.model_dump_json()}"
		)

		if (
			parsed_payload.source == "cron"
			or parsed_payload.source == "admin"
			and parsed_payload.geometry is None
		):
			logger.info(f"Loading GeoDataFrame from {COFFEE_SHP}")
			gdf = gpd.read_file(COFFEE_SHP)
		else:
			logger.info("Loading GeoDataFrame from payload geometry")
			gdf = gpd.GeoDataFrame.from_features(parsed_payload.geometry)

		return f"Received WTSS task with payload: {parsed_payload.model_dump_json()}"

		run_wtss(
			gdf=gdf,
			start_date=parsed_payload.start_date,
			end_date=parsed_payload.end_date,
		)
		return "WTSS task finished successfully."
	except Exception as e:
		logger.error(f"Error processing WTSS task: {e}", exc_info=True)
		raise  # FAILURE


@app.task
def handle_stac(payload: dict):
	"""
	Processing task for STAC queue messages.

	:param payload: The payload containing STAC task details
	:type payload: dict
	:return: Confirmation message
	:rtype: str
	"""
	try:
		parsed_payload: BDCBasePayload = parse_stac_payload(payload)

		logger.info(
			f"Received STAC task with payload: {parsed_payload.model_dump_json()}"
		)

		gdf = gpd.read_file(CAMPO_VERTENTES_SHP)

		run_stac(
			gdf=gdf,
			start_date=parsed_payload.start_date,
			end_date=parsed_payload.end_date,
		)
		return "STAC task finished successfully."
	except Exception as e:
		logger.error(f"Error processing STAC task: {e}", exc_info=True)
		raise  # FAILURE
