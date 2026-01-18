from os import getenv as env
from pathlib import Path

import geopandas as gpd
from celery.utils.log import get_task_logger

from models.bdc import BDCBasePayload, WTSSPayload, parse_wtss_payload
from src.services.wtss_service import run_wtss
from src.worker import app

logger = get_task_logger(__name__)

DATA_DIR = Path(env("COFFEE_SHAPEFILE_PATH"))


@app.task
def handle_stac(payload: dict):
	"""
	Task para processar mensagens da fila STAC.
	"""
	logger.info(f"Received STAC task with payload: {payload}")
	# TODO: Adicionar lógica para processar imagens via STAC.
	return f"STAC task processed for payload: {payload}"


@app.task
def bdc_cron():
	"""
	Task Celery para enfileirar o job WTSS e STAC.
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
	Task para processar mensagens da fila WTSS.
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
			logger.info(f"Loading GeoDataFrame from {DATA_DIR}")
			gdf = gpd.read_file(DATA_DIR)
		else:
			logger.info("Loading GeoDataFrame from payload geometry")
			gdf = gpd.GeoDataFrame.from_features(parsed_payload.geometry)

		run_wtss(
			gdf=gdf,
			start_date=parsed_payload.start_date,
			end_date=parsed_payload.end_date,
		)
		return "WTSS task finished successfully."
	except Exception as e:
		logger.error(f"Error processing WTSS task: {e}", exc_info=True)
		raise  # FAILURE
