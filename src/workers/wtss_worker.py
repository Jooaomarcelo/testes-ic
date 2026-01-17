import asyncio
import logging
from os import getenv as env
from pathlib import Path

import geopandas as gpd

from src.models.wtss import WTSSPayload, parse_wtss_payload
from src.queues.client import PikaClient
from src.services.wtss_service import run_wtss
from src.utils.logging import setup_logging

QUEUE_NAME = "bdc.wtss"
DATA_DIR = Path(
	env("COFFEE_SHAPEFILE_PATH", "/app/src/data/ig_cafe/bom_sucesso_2022.shp")
)
# Configure logging
logger = setup_logging()
logger = logging.getLogger(__name__)


async def handle_message(payload: bytes):
	payload: WTSSPayload = parse_wtss_payload(payload)
	logger.info(f"Received message on queue {QUEUE_NAME}: {payload.model_dump()}")

	if payload.source == "cron":
		logger.info(f"Loading GeoDataFrame from {DATA_DIR}")
		gdf = gpd.read_file(DATA_DIR)
	else:
		logger.info("Loading GeoDataFrame from payload geometry")
		gdf = gpd.GeoDataFrame(payload.geometry)

	run_wtss(
		gdf=gdf,
		start_date=payload.start_date,
		end_date=payload.end_date,
	)


async def main():
	client = PikaClient()
	await client.connect()

	try:
		await client.consume(
			queue_name=QUEUE_NAME,
			process_callable=handle_message,
			prefetch_count=5,
		)
	except asyncio.CancelledError:
		print("Shutting down consumer...")
	finally:
		await client.close()


if __name__ == "__main__":
	asyncio.run(main())
